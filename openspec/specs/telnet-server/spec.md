# telnet-server Specification

## Purpose

Defines how the Pico accepts telnet connections, reads player input as clean
lines, and writes output to many long-lived clients without one client
blocking the others.

## Requirements

### Requirement: Controller-facing transport interface
The telnet transport SHALL deliver accepted connections, decoded input lines,
capacity rejections, idle expiry and disconnect events to an application
controller. The controller SHALL interpret commands and request text from a
view before sending it through the transport's buffered output interface.
The transport SHALL NOT interpret game commands, render application messages,
or access database records or dirty flags. Views SHALL return text without
writing sockets or changing model state.

#### Scenario: Command reaches the controller
- **WHEN** a client sends `/QUIT` followed by a line ending
- **THEN** the transport delivers the decoded line to the controller
- **AND** the controller requests the view's goodbye text and a transport close

#### Scenario: Capacity notice uses the same presentation path
- **WHEN** a connection exceeds the client limit
- **THEN** the transport reports the rejection to the controller
- **AND** the controller supplies the view's server-full text for the transport
  to send before closing, without creating an application session

#### Scenario: Application output needs no client input
- **WHEN** a controller requests text for a connected client between input lines
- **THEN** the transport queues and sends it without waiting for another command

### Requirement: Application timer hook
The transport SHALL expose a periodic controller notification while serving
clients, including when no clients are connected. It SHALL NOT perform
database saves or inspect model dirty state itself. The application controller
SHALL use the hook for response delivery and model-owned periodic saves.

#### Scenario: Bootstrap runtime has no database side effects
- **WHEN** the transport runs with a controller that schedules no database work
- **THEN** periodic notifications cause no database operations in the transport

#### Scenario: Dirty save without clients
- **WHEN** a save interval elapses with dirty models and no connected clients
- **THEN** the application controller requests their save operations

### Requirement: Listen for telnet clients
After the hotspot is up, the system SHALL accept TCP connections on
`TELNET_PORT` on all interfaces and keep each connection open until the client
disconnects, the client quits, or the server closes it.

#### Scenario: Connect with telnet
- **WHEN** a client runs `telnet 192.168.4.1 8888`
- **THEN** the connection is accepted and stays open

### Requirement: Welcome and prompt
On a new connection the system SHALL present login/guest instructions and a
prompt, preceded by the user's seven-line PICO MUD block-art banner, preserving
its UTF-8 characters, spacing and line breaks. After successful registered login or guest entry it SHALL send
WELCOME_TEXT, navigation instructions, room 1's description and a prompt.
Prompted password entry SHALL use a password prompt, without requiring masking.
Completed command responses SHALL end with a prompt unless closing the session.

#### Scenario: New connection
- **WHEN** a client connects
- **THEN** it receives the seven-line PICO MUD banner followed by
  `/connect <name> [password]` and `/connect guest`
  instructions and a prompt; it is not yet present in a room

#### Scenario: Enter world
- **WHEN** the client successfully authenticates or chooses guest
- **THEN** it receives the configured welcome, instructions and room 1 view

### Requirement: Client limit
The system SHALL allow at most `MAX_CLIENTS` connections at once. A connection
beyond the limit SHALL receive a short "server full" message and then be
closed. Existing clients SHALL NOT be affected.

#### Scenario: Server full
- **WHEN** `MAX_CLIENTS` clients are connected and one more connects
- **THEN** the new client sees a "server full" message and is disconnected,
  and the others stay connected

### Requirement: Telnet negotiation filtering
The system SHALL remove telnet command sequences (IAC, byte 255, with their
option bytes, including subnegotiation blocks) from the input before it is
treated as text. It SHALL NOT answer negotiation requests in this change.

#### Scenario: Client sends negotiation on connect
- **WHEN** a telnet client sends option negotiation bytes and then types
  `hello`
- **THEN** the line received by the server is exactly `hello`

### Requirement: Line input
The system SHALL split input into lines on LF, and SHALL treat CRLF and a
lone CR followed by NUL as one line ending. Backspace (8) and DEL (127) SHALL
remove the last character of the current line (a whole UTF-8 character, not a
single byte). Other control characters SHALL be dropped. Input SHALL be
decoded as UTF-8 and invalid byte sequences SHALL be dropped. Transport SHALL
preserve surrounding whitespace for the controller to interpret: command
whitespace is trimmed, while a prompted password retains exact printable text.
An empty gameplay command SHALL only produce a new prompt.

#### Scenario: Non-ASCII input
- **WHEN** a client types `hälsa på dig` and presses enter
- **THEN** the server receives the line `hälsa på dig`

#### Scenario: Backspace over a multibyte character
- **WHEN** a client types `abö`, then backspace, then `c`, then enter
- **THEN** the server receives `abc`

#### Scenario: LF-only client
- **WHEN** a client ends lines with LF only
- **THEN** lines are received the same as with CRLF

#### Scenario: Password whitespace
- **WHEN** a prompted password contains leading or trailing spaces
- **THEN** authentication uses those spaces rather than silently trimming them

### Requirement: Line length limit
The system SHALL keep at most MAX_LINE_LENGTH bytes of one input line and
discard additional bytes until its delimiter. It SHALL report truncation to
the controller, which SHALL reject that whole command or password with a
line-too-long error. Truncated commands SHALL NOT mutate state or authenticate.
The next valid line SHALL be processed normally on the same connection.

#### Scenario: Overlong line
- **WHEN** a client sends a line longer than MAX_LINE_LENGTH bytes
- **THEN** the line is rejected instead of executing a truncated prefix
- **AND** the connection stays open for the next line

### Requirement: Non-blocking output
Output to each client SHALL go through that client's own bounded buffer and
be sent without blocking the event loop. Lines SHALL be UTF-8 encoded with
CRLF endings. Controllers SHALL deliver large legitimate command responses
incrementally as capacity becomes available, rather than enqueue them whole.
A client that stops reading SHALL NOT delay other clients. An attempted raw
enqueue beyond the fixed transport limit SHALL still disconnect that client.

#### Scenario: Slow client
- **WHEN** one client stops reading while others keep typing
- **THEN** the other clients keep getting responses without delay

#### Scenario: Output buffer overflow
- **WHEN** an enqueue attempts to exceed a client's maximum pending output
- **THEN** that client is disconnected and the server keeps running

#### Scenario: Long response
- **WHEN** help or a room listing exceeds the transport buffer size
- **THEN** the controller feeds chunks as space becomes available and sends a
  final prompt without overflowing or creating an unbounded response backlog

### Requirement: Idle timeout
The system SHALL close a connection that has sent no input for
`IDLE_TIMEOUT` seconds, after sending a short message saying it was
disconnected for inactivity.

#### Scenario: Idle client
- **WHEN** a client sends nothing for `IDLE_TIMEOUT` seconds
- **THEN** it receives an inactivity message and is disconnected

### Requirement: Quit command
The system SHALL understand `/quit` case-insensitively before login and during
gameplay, send goodbye and close the connection. During a password prompt the
next line SHALL instead be treated as password data. Valid gameplay commands
SHALL dispatch to their controllers; unrecognized commands SHALL report an
error and help hint while preserving the connection.

#### Scenario: Quit
- **WHEN** a client types `/QUIT` at the login or gameplay command prompt
- **THEN** it receives a goodbye message and the connection is closed

#### Scenario: Other input
- **WHEN** an authenticated player types `/look`
- **THEN** it receives the current room view and a new prompt

#### Scenario: Unknown command
- **WHEN** a player types an unrecognized command without a matching local action
- **THEN** it receives an unknown-command error and a new prompt

### Requirement: Connection error isolation
An error while handling one connection SHALL be printed to the serial console
and SHALL close only that connection. The server and other clients SHALL keep
running.

#### Scenario: Client resets connection
- **WHEN** a client's connection is reset mid-session
- **THEN** its slot is freed and other clients are unaffected

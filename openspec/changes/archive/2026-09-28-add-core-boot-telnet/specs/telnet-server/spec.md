# Spec Delta

## Purpose

Defines how the Pico accepts telnet connections, reads player input as clean
lines, and writes output to many long-lived clients without one client
blocking the others.

## ADDED Requirements

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
database saves or inspect model dirty state itself. Database features remain
outside this change.

#### Scenario: Bootstrap runtime has no database side effects
- **WHEN** the bootstrap server runs through repeated timer notifications
- **THEN** the controller receives the notifications and the server creates or
  modifies none of `users.json`, `rooms.json` or `mail.json`

### Requirement: Listen for telnet clients
After the hotspot is up, the system SHALL accept TCP connections on
`TELNET_PORT` on all interfaces and keep each connection open until the client
disconnects, the client quits, or the server closes it.

#### Scenario: Connect with telnet
- **WHEN** a client runs `telnet 192.168.4.1 8888`
- **THEN** the connection is accepted and stays open

### Requirement: Welcome and prompt
On a new connection the system SHALL send `WELCOME_TEXT` followed by the
prompt `> `. After the output for each input line it SHALL send the prompt
again.

#### Scenario: New connection
- **WHEN** a client connects
- **THEN** it receives the welcome text and then `> `

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
decoded as UTF-8 and invalid byte sequences SHALL be dropped. Leading and
trailing whitespace SHALL be stripped, and empty lines SHALL only produce a
new prompt.

#### Scenario: Non-ASCII input
- **WHEN** a client types `hälsa på dig` and presses enter
- **THEN** the server receives the line `hälsa på dig`

#### Scenario: Backspace over a multibyte character
- **WHEN** a client types `abö`, then backspace, then `c`, then enter
- **THEN** the server receives `abc`

#### Scenario: LF-only client
- **WHEN** a client ends lines with LF only
- **THEN** lines are received the same as with CRLF

### Requirement: Line length limit
The system SHALL keep at most `MAX_LINE_LENGTH` bytes of one input line. Any
bytes beyond that, up to the line ending, SHALL be discarded, and the
truncated line SHALL still be processed. A line is never cut in the middle of
a UTF-8 character.

#### Scenario: Overlong line
- **WHEN** a client sends a line longer than `MAX_LINE_LENGTH` bytes
- **THEN** only the first `MAX_LINE_LENGTH` bytes (rounded down to a whole
  character) are processed and the connection stays open

### Requirement: Non-blocking output
Output to each client SHALL go through that client's own buffer and be sent
without blocking the event loop. Output lines SHALL be UTF-8 encoded with CRLF
line endings. A client that stops reading SHALL NOT delay input or output for
other clients. If a client's pending output grows beyond a fixed maximum
buffer size, that client SHALL be disconnected.

#### Scenario: Slow client
- **WHEN** one client stops reading while others keep typing
- **THEN** the other clients keep getting responses without delay

#### Scenario: Output buffer overflow
- **WHEN** a client's unsent output exceeds the maximum buffer size
- **THEN** that client is disconnected and the server keeps running

### Requirement: Idle timeout
The system SHALL close a connection that has sent no input for
`IDLE_TIMEOUT` seconds, after sending a short message saying it was
disconnected for inactivity.

#### Scenario: Idle client
- **WHEN** a client sends nothing for `IDLE_TIMEOUT` seconds
- **THEN** it receives an inactivity message and is disconnected

### Requirement: Quit command
Until the command set exists, the system SHALL understand `/quit`
(case-insensitive), which sends a goodbye message and closes the connection.
Any other non-empty line SHALL get the reply `Unknown command. Type /quit to
leave.` followed by the prompt.

#### Scenario: Quit
- **WHEN** a client types `/QUIT`
- **THEN** it receives a goodbye message and the connection is closed

#### Scenario: Other input
- **WHEN** a client types `/look`
- **THEN** it receives the unknown command reply and a new prompt

### Requirement: Connection error isolation
An error while handling one connection SHALL be printed to the serial console
and SHALL close only that connection. The server and other clients SHALL keep
running.

#### Scenario: Client resets connection
- **WHEN** a client's connection is reset mid-session
- **THEN** its slot is freed and other clients are unaffected

# Design

## Context

`target/main.py` is empty; no application has been implemented.
`openspec/reference-project` (the pi-room project) shows
patterns that work on the Pico 2 W: starting an AP with
`network.WLAN(network.WLAN.IF_AP)`, a `select.poll` event loop with
non-blocking sockets, `gc.collect()` about every 5 seconds, and LED blink
codes. But it serves HTTP, where each request gets one reply and the socket is
closed. It calls `sendall` inside the handler, and it runs a DNS server in a
second thread. A MUD keeps connections open, has to write to many clients at
any time, and must not run DNS, so the loop is reused as a pattern only and
the I/O layer is new. Motivation is in proposal.md; required behaviour is in
the specs. Its `messages_controller.py` combines data storage, request handling
and rendering. The MUD separates those responsibilities into models,
controllers and views, as requested in `PROJECT_OUTLINE.md`.

## Goals / Non-Goals

**Goals:**
- A single-threaded event loop that later changes can extend (login, command
  dispatch, the periodic save) without restructuring.
- A clean boundary: the telnet layer turns raw bytes into text lines and text
  into bytes, and knows nothing about game logic.
- All application interaction with telnet passes through controllers. Views
  format text; models own persistent data and dirty flags.

**Non-Goals:**
- Telnet option negotiation (NAWS, echo, charset). Echo suppression for
  passwords comes with login.
- Threads, `asyncio`, and `.mpy` precompilation. `.mpy` is recommended in
  the outline, but this change is small enough to run from source.
- User, room, item and mail model implementations or database saves. Their
  boundaries are established here for subsequent feature changes.

## Decisions

### 1. MVC layout and dependency wiring
```
target/
  config.py                       settings only, at the device root
  main.py                         validation, boot and dependency wiring
  modules/
    __init__.py
    led.py                        LED helpers and fatal blink loop
    wifi.py                       AP startup utility
    telnet.py                     Client buffers/parser; TelnetServer poll loop
  controllers/
    __init__.py
    telnet_controller.py          TelnetController: events and command dispatch
  views/
    __init__.py
    telnet_view.py                text-formatting functions
```

`main.py` imports root-level `config`, validates settings, constructs the
controller with its view, and passes the controller to the telnet module.
Utilities do not import concrete controllers. Controller callbacks are injected
so there is no circular import or global handler registry.

The controller interprets commands and coordinates responses. Views take
values and return Unicode text, without reading models or calling sockets.
Only controllers request application output or disconnects through the
transport API. The telnet module retains responsibility for protocol handling,
socket cleanup and transport limits. `config.py` has no model or controller state.

Future features add `models/users.py`, `models/rooms.py`, `models/items.py` and
`models/mail.py`, plus feature controllers and views. These files are not
scaffolded or imported by this first change. One application-lifetime instance
of each model will be shared across controllers, never one database per client.
This explicit layout replaces the earlier plan for flat `state.py` and
`commands.py` modules without introducing an MVC framework.

### 2. One thread, one `select.poll` loop
All sockets are non-blocking and registered with one `poll` object. Each
iteration:
1. Run `poll(100 ms)`.
2. Accept new connections, and read from readable clients.
3. Hand each complete line to the controller.
4. Flush output buffers, registering `POLLOUT` only for clients with pending
   output.
5. Report idle clients to the controller, finish scheduled closes, invoke a
   controller tick with monotonic time, and run `gc.collect()` every ~5 s.

The 100 ms tick gives later changes a place for timers such as the 30-second
save check. The transport does not inspect model state or dirty flags: a later
application controller uses the tick to invoke model save operations.
`asyncio` was considered: it is available in MicroPython, but it
costs more RAM and hides the timing, and the reference poll pattern is
already known to work on this board. Threads were rejected because the second
core would need locks around all state.

### 3. Controller and view interface
`modules.telnet.TelnetServer(controller)` reports events to
`controllers.telnet_controller.TelnetController`:

| Callback | Responsibility |
|---|---|
| `on_connect(client)` | Send the view's welcome text and prompt |
| `on_line(client, text)` | Trim command whitespace, dispatch `/quit`, handle empty/unknown input, send view output |
| `on_reject(client, reason)` | Render the server-full response and request a close |
| `on_timeout(client)` | Render the idle message and request a close |
| `on_disconnect(client, reason)` | Release controller session references; later notify other players |
| `on_tick(now_ms)` | Application timer hook; a no-op until scheduled application work exists |

The client exposes `send(text)` and `close(message=None)` to the controller.
Views supply welcome, prompt, goodbye, unknown-command, full-server and idle
text. They return text only; the controller chooses the recipient and calls
the transport API. A future model result likewise travels through a
controller and a view before being sent. Models never send telnet output.

The module detects capacity, inactivity and socket errors. It reports reasons
rather than embedding user-facing messages or command names. Socket failures
and output overflow can force immediate cleanup, with a disconnect callback;
there is no obligation to deliver text over an unusable connection.
Rejected sockets do not become active sessions and cannot accumulate an
unbounded rejection queue. Their controller-generated response is best effort.

Callbacks keep socket scheduling in the transport while giving application
policy and presentation clear owners. The controller can delegate later
commands to feature controllers without changing the byte parser.

Later notifications use `controllers/notification_controller.py` with the
session controller's shared live sessions. It selects one session, one room
or all players, formats text through a notification view, and calls the same
buffered send interface. Scanning up to `MAX_CLIENTS` sessions avoids a second
room-membership registry or channel subscriptions. Transport has no knowledge
of room ids, users or notification types. The current spec's "Application
output needs no client input" scenario and task 6.1 cover this prerequisite;
notification routing and its controllers/views are deferred until sessions
and gameplay exist. See the outline's Notifications section for the rules.

The bootstrap controller shows `WELCOME_TEXT` on connection for this change.
Once login exists, the session controller will show it after login as required
by the project outline.

### 4. Output buffering
`client.send(text)` encodes to UTF-8, converts `\n` to `\r\n`, and appends to
a `bytearray`. The flush step calls `sock.send(buf)`, which may send only part
of the buffer (a short write) or raise `EAGAIN`, and removes whatever was
sent. `sendall` is not used: the MicroPython docs say its behaviour on
non-blocking sockets is undefined. When a buffer exceeds `MAX_OUTPUT_BUFFER`
(4 KB, a module constant rather than a config value), that client is
disconnected. This bounds pending output to about `MAX_CLIENTS` × 4 KB,
excluding socket and input overhead. `close()` schedules a drain then closes;
it never blocks. Use a short bounded drain deadline so a non-reading peer
cannot retain a closing connection indefinitely. The controller supplies any
goodbye or idle text; the module only encodes and queues it.

### 5. Input parsing as a byte state machine
Each client keeps a parser state (`DATA`, `IAC`, `OPT`, `SB`, `SB_IAC`) and a
line `bytearray`:
- IAC WILL/WONT/DO/DONT consume one option byte.
- A subnegotiation (`SB ... IAC SE`) is skipped entirely.
- `IAC IAC` is a literal 255, which is invalid on its own in UTF-8 and is
  therefore dropped.
- Track a pending CR across receives: LF ends a line; CRLF and CR NUL each
  finish one line, as required by the existing input spec.
- BS/DEL remove bytes from the end of the line: continuation bytes
  (`0b10xxxxxx`) and then the lead byte, so a whole character is removed.
- Other bytes below 32 are dropped.
- Bytes past `MAX_LINE_LENGTH` are dropped until the next line ending.

When a line ends, the parser decodes it. MicroPython's `bytes.decode` has no
`errors="ignore"`, so invalid bytes are removed with a small validator before
decoding. The alternative, try/except around decode that drops the whole line
on failure, loses user input. Truncating at the byte limit is followed by
trimming an incomplete trailing sequence. The module delivers complete text
lines, including empty lines, to the controller. Whitespace trimming and
command interpretation belong to the controller.

### 6. Hotspot security
`ap.config(ssid=ssid, password=password, security=0x00400004)` is called before
`ap.active(True)`. CYW43 source confirms that `password` and `key` are aliases,
but setting the AP password does not select security. Explicit WPA2 AES avoids
depending on prior radio state. Startup verifies the configured security and
address. This API succeeded on the connected Pico 2 W with MicroPython 1.29.0;
external password association remains a user check (task 3.2). Source excerpts
and results are in `documentation/micropython-network-wlan.md`.

The AP utility establishes and verifies 192.168.4.1, as required by the fixed
address spec. It must not continue with a different address; failure to
establish the required address is a boot error.

### 7. Boot and fatal handling in `main.py`
Validate root-level `config`, start the AP through `modules.wifi`, and signal
one blink through `modules.led`. Construct the view/controller and telnet
server, bind the listener, then signal two blinks and steady on before entering
the poll loop. A blocking `run()` must not precede the server-ready LED signal.

On a fatal exception, close transport resources, print the traceback and enter
`modules.led.fatal_loop()`.
`validate` raises `ValueError("AP_PASSWORD must be 8-63 characters")` and
similar errors. Per-client errors are caught inside the loop (Decision 2), so
only loop-level failures reach this handler. `KeyboardInterrupt` (Ctrl-C over
the REPL) is re-raised so the admin can still reach the REPL during
development.

### 8. Future models and model-owned dirty state
This is the project-wide contract for later data features, not additional
database implementation in this change:

| Model | Authoritative data | Dirty state and save owner |
|---|---|---|
| `models/users.py` | User records, credentials, home references and flags | Owns `users.json` and its dirty flag |
| `models/rooms.py` | Room records, exits and nested item storage | Owns `rooms.json` and its shared dirty flag |
| `models/items.py` | Item and interaction operations over the rooms model's nested storage | Marks the rooms model dirty; no separate file or flag to clear |
| `models/mail.py` | User inboxes | Owns `mail.json` and its dirty flag |

The items model receives the shared rooms model. It identifies an item by
`(room_id, item_id)`, enforces item/interaction limits, and performs moves as
removal plus recreation with a destination-local id. Validate ownership,
destination capacity and the new record before removing the source. Successful
mutations mark the shared rooms save unit dirty. Reading an item or displaying
its interaction text does not. Rooms and items are serialized together once,
without duplicate storage or competing writers.

Controllers call model operations instead of mutating returned records or
toggling dirty flags. Models enforce record invariants; controllers check the
acting player's permissions and coordinate operations spanning models. Views
receive only the values needed for display. Online presence and current player
locations remain controller session state and never dirty database models.

A later controller schedules the 30-second save check from `on_tick`, or runs
it immediately for `/save`. It invokes `save_if_dirty()` on users, rooms and
mail. Each model streams its data to a temporary file, replaces its file, then
clears its dirty flag only on success. Failures retain the flag for retry.
The items model has no independent save step. This replaces a monolithic global
state/dirty registry and keeps file ownership inside the model layer.

## Risks / Trade-offs

- [Firmware security constant differs] → Verified on the device in tasks;
  documented fallback to the explicit cyw43 constant.
- [The 4 KB output cap disconnects a client during a large burst of output] →
  Enough for a screen of text; later changes can raise the module constant.
- [`poll` with `POLLOUT` on lwIP sockets behaves differently from CPython] →
  Flush is also attempted on every tick for clients with pending data, so
  the design does not depend only on `POLLOUT`.
- [Running from source costs RAM at import] → Acceptable at this size;
  `.mpy` can be added later.
- [No automated tests] → Every task has a manual on-device check with
  `telnet`/`nc` and the serial REPL.

## Migration Plan

This is a new install with nothing to migrate. Deploy with
`mpremote cp -r target/* :` (or Thonny), then `mpremote reset`. To roll back,
delete the files from the device.

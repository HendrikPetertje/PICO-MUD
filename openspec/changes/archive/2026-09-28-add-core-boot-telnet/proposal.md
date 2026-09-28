# Proposal

## Why

`target/main.py` is empty, so nothing runs on the Pico yet. Every later feature
(login, rooms, items, mail, persistence) needs the same base: a configuration
file, a password-protected wifi hotspot, and a non-blocking telnet server that
keeps connections open and can push text to any client. Building and checking
that base on the device first keeps the later changes focused on game logic.

## What Changes

- Add `target/config.py` with every setting from the project outline: network
  and server settings, admin account, salt, welcome text, save interval, data
  limits and memory threshold, plus the fixed `MAX_LINE_LENGTH` constant. The
  values are defined now even though only some are used by this change.
- Validate the configuration at boot. An invalid `AP_PASSWORD` (not 8-63
  characters) is a fatal error.
- Add the boot sequence in `target/main.py`: start a WPA2-protected hotspot
  named `AP_SSID` at 192.168.4.1, then start the telnet server.
- Establish MVC boundaries: utilities in `target/modules/`, application
  interactions in `target/controllers/`, and text formatting in `target/views/`.
  Keep `config.py` at the device root and `main.py` focused on boot and wiring.
- Add a single-threaded, poll-based `target/modules/telnet.py` on `TELNET_PORT`:
  - accepts up to `MAX_CLIENTS` connections and refuses extra ones politely;
  - filters telnet negotiation (IAC) sequences out of the input;
  - reads UTF-8 lines with CRLF/LF endings and backspace handling;
  - caps lines at `MAX_LINE_LENGTH` bytes;
  - gives every client its own non-blocking output buffer;
  - disconnects clients after `IDLE_TIMEOUT` seconds of inactivity.
- Route all application-facing telnet events through a telnet controller,
  including connection admission, input, timeout and disconnect events.
  The controller obtains text from a telnet view and sends it through the
  transport's buffered interface; neither transport nor views access models.
- Through that controller, show `WELCOME_TEXT` and the `> ` prompt on connect.
  For now only `/quit` is understood; every other line gets a placeholder
  "unknown command" reply.
  The full command set arrives in later changes.
- Show status on the onboard LED: 1 blink when the hotspot is up, 2 blinks and
  then steady on when the server is running, 3 blinks repeating on a fatal
  error. Fatal errors are printed with their traceback to the serial console.
- Run `gc.collect()` regularly from the event loop.
- Document the future `models/` boundary: users, rooms and items-in-rooms
  models, plus a mail model for `mail.json`. Models own database data and
  dirty state. Item changes mark the rooms model dirty because items remain
  nested in `rooms.json`; no duplicate item database is introduced.

Out of scope, covered by later changes: login and guests, sessions tied to
users, room/item/user/mail model implementations, data files and persistence,
game commands, mail, and hiding password input (`IAC WILL ECHO`), which is only
needed once login exists.
Room/chat notifications and their session and notification controllers also
arrive with those features. This change provides their prerequisite:
controller-driven buffered output that does not wait for client input, as
covered by the telnet spec and manual acceptance tasks. It adds no channels
or subscription system.
There is no DNS, captive portal or HTTP, and no automated tests.

## Capabilities

### New Capabilities
- `configuration`: the settings file on the device, its defaults and its
  boot-time validation.
- `wifi-hotspot`: the WPA2 access point the Pico creates at boot.
- `telnet-server`: accepting and managing telnet connections, reading input
  lines and writing output to clients through a controller-facing transport
  interface. MVC layout and future model ownership are specified in the design.
- `device-status`: LED status patterns and fatal error reporting over serial.

### Modified Capabilities
None. There are no existing specs.

## Impact

- Planned files: `target/config.py`, `target/main.py`, utilities
  `target/modules/{wifi,led,telnet}.py`,
  `target/controllers/telnet_controller.py` and `target/views/telnet_view.py`,
  with package initializers. The model layout is documented for later changes.
- Relies only on MicroPython built-ins: `network`, `socket`, `select`,
  `machine`, `gc`, `time` and `sys`. No third-party dependencies.
- `openspec/reference-project` is used for reference only and is not changed.
- On the device this uses one TCP port (8888 by default) and the wifi radio in
  AP mode.

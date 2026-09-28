# Tasks

Implementation follows the MVC boundaries in `design.md`. Model ownership is
documented for later features; this change implements boot utilities, the
telnet transport, its controller and its text view. Verification below is
manual; no unit or integration test suite is required.

Hardware handoff: the user handles Wi-Fi association, external telnet clients
and visual LED confirmation. USB upload and serial checks can be performed
without switching the development computer away from its internet connection.
Unchecked tasks may have implementation delivered but still await the exact
manual acceptance checks described below.

User acceptance (2026-09-28): LED patterns, Wi-Fi startup and WPA are confirmed.
The user accepted all section 4 tasks for now; task 4.3 is closed on that basis,
not as a claim that every on-device callback/error case was independently run.
The user subsequently confirmed tasks 2.2, 5.2, 6.1 and 6.2 succeeded and
requested archiving. All remaining manual acceptance checks are closed on
that user confirmation.

## 1. Layout and configuration

- [x] 1.1 Create `target/modules/`, `target/controllers/` and `target/views/` with package initializers, keeping `target/main.py` and `target/config.py` at the root. Verify the deployed package paths match design Decision 1 and contain no duplicate root-level wifi, LED or telnet implementations.
- [x] 1.2 Define every setting in `target/config.py` from the configuration spec and outline, including the fixed byte limit and public-defaults warning. Verify in the device REPL that `import config` exposes all settings and that this file contains no application state or dirty flags.
- [x] 1.3 Add boot validation in `main.py`, keeping `config.py` settings-only. Verify manually that the default settings pass and an invalid password or nonpositive server limit raises an error naming the setting before AP startup.
- [x] 1.4 Align the outline's architecture section and `documentation/mvc-boundaries.md` with the delivered package layout. Verify they identify users, rooms, items and mail as future models, shared rooms/items dirty state, and controller-only application access to telnet.

## 2. LED and fatal handling

- [x] 2.1 Implement `target/modules/led.py` with blink, steady-on and repeating fatal-pattern helpers. Verify the one-blink, two-blink and repeating three-blink patterns manually on the Pico.
- [x] 2.2 Add the fatal boundary in `main.py`, using the LED utility and serial traceback reporting while allowing Ctrl-C to reach the REPL. Verify an invalid configuration produces a traceback and repeating three-blink pattern; restore the configuration afterwards.

## 3. Wifi utility

- [x] 3.1 Implement AP startup in `target/modules/wifi.py`, with root config values, a 10-second activation deadline and the required address 192.168.4.1. Wire successful startup to the one-blink signal. Verify the serial SSID/address, DHCP assignment and fixed-address requirement on the device; do not silently continue at another address.
- [x] 3.2 Verify the installed firmware's WPA2 configuration using `documentation/micropython-network-wlan.md` and the firmware's supported API. Record the working API and firmware version in that document; verify correct-password association succeeds and wrong-password association fails.

## 4. Telnet transport module

- [x] 4.1 Implement `Client` in `target/modules/telnet.py` with UTF-8/CRLF output, partial writes, EAGAIN handling, a 4096-byte output cap and non-blocking close/drain with a bounded deadline. Keep message text outside the module. Verify manually via the REPL that complete and partial output is retained correctly and a non-reading peer cannot block close or other clients.
- [x] 4.2 Implement incremental IAC filtering, line framing, whole-character backspace, invalid UTF-8 filtering and byte-limited input. Deliver decoded lines to the controller without command interpretation or whitespace policy. Verify manually by feeding split byte sequences in the REPL, including `äöå`, BS/DEL, CRLF, LF, CR NUL and an overlong line; inspect the decoded results rather than relying on the terminal's local echo.
- [x] 4.3 Implement `TelnetServer(controller)` with non-blocking accept/read/write, capacity checks, timeout detection, controller callbacks from design Decision 3, disconnect cleanup and per-client error isolation. Expose listener startup separately from the blocking loop. Verify by source inspection that the module imports no concrete controller, view or model and contains no command routing or application response strings; manually confirm callback ordering and cleanup with the device REPL.
- [x] 4.4 Add periodic controller ticks and regular garbage collection using monotonic elapsed time. Verify ticks continue without clients and that the module contains no database filenames, saves or dirty-state checks.
- [x] 4.5 Update the local transport notes with the final callback contract, framing decisions and close/drain behavior; verify those notes agree with the controller-facing spec and delivered transport API.

## 5. Telnet controller, view and boot wiring

- [x] 5.1 Implement `target/views/telnet_view.py` as text-formatting functions for welcome, prompt, goodbye, unknown command, server full and inactivity. Verify the returned strings manually, including Unicode content, and inspect that the view has no socket access, model mutation or database writes.
- [x] 5.2 Implement `target/controllers/telnet_controller.py` with all callbacks from design Decision 3. Keep whitespace handling, case-insensitive `/quit`, empty/unknown input and response selection here; use view text through client send/close, and leave the tick callback a no-op. Verify a connected client receives the specified welcome, prompt and replies, and `/QUIT` disconnects it; inspect that the controller neither stores database records nor manages dirty flags.
- [x] 5.3 Wire config, utilities, view and controller in `main.py`; bind the listener before the two-blink/steady-on signal, then run the loop. Verify normal startup reaches that LED state, serial reports the listening port, and application messages originate through the controller/view path.
- [x] 5.4 Add deployment instructions for root files and nested packages to the outline and documentation index. Verify the documented upload preserves `modules/`, `controllers/` and `views/` at the device root and all imports succeed; record the actual firmware/version used for the manual checks.

## 6. End-to-end manual acceptance

- [x] 6.1 Exercise all telnet spec scenarios on the Pico: negotiation, line framing, Unicode and backspace, overflow, multiple clients, server-full response, idle timeout, abrupt disconnect and controller-originated output between input lines. Verify one slow or failed client does not stall others; restore any temporarily lowered limits.
- [x] 6.2 Cold boot and verify LED order, serial progress, password-protected association, address 192.168.4.1 and no listener on port 80. Record available heap and firmware in the change's documentation; verify repeated ticks and connections create or modify no database files.

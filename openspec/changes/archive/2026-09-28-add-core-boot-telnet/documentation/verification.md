# Verification and handoff — 2026-09-28

## Device

- Raspberry Pi Pico 2 W with RP2350, MicroPython 1.29.0 dated 2026-08-24.
- USB serial `/dev/cu.usbmodem2101`; initially empty filesystem.
- Uploaded root config/main and modules/controllers/views packages using the
  command in the documentation index. All package imports succeeded on-device.
- Captured normal boot: WPA2 AES AP at 192.168.4.1, telnet port 8888, free heap
  **431200 bytes** after startup and garbage collection. This is a measured
  bootstrap baseline, not a memory guarantee for later game data.
- Device left running the normal application after checks. Diagnostic scripts
  ran from the host through USB and were not installed on the board.

## Passed via USB on the Pico

- All config names and defaults import; invalid password/positive-integer
  limits rejected with the setting name. Config has no database state.
- UTF-8 split between receives, äöå and emoji backspace, BS/DEL, LF/CRLF/CR NUL,
  split IAC/subnegotiation, invalid UTF-8, input truncation and empty lines.
- Output encoding/CRLF, synthetic short writes and EAGAIN, output overflow,
  bounded close deadline. Actual slow network peers still need acceptance.
- Plain-text view output and MVC source boundaries.
- AP configuration readback is `0x400004`, address is 192.168.4.1; listener binds.
- Periodic controller tick runs without clients; transport contains no database
  access. No users.json, rooms.json or mail.json was created.

## Passed locally with real host TCP sockets

Temporary CPython adapter supplied MicroPython clock and poll conventions;
the deployed transport/controller/view code handled welcome, empty/unknown
commands, asynchronous output, two clients, excess-client rejection, `/QUIT`,
idle expiry and abrupt disconnect. This verifies application socket flow but
does not replace Pico network checks. No permanent test suite was added.

Attempts to connect the Pico to its own listener failed (127.0.0.1:
EHOSTUNREACH; AP address: ECONNABORTED), so those were not counted as successful
on-device client checks.

## User confirmation and acceptance

The user subsequently confirmed successful Wi-Fi association with the default
password and external telnet delivery of the welcome text and newlines.
The roughly 30-second delay occurred in Blink on the iPad before "Trying";
another client connected in under one second. The user asked to ignore that
client-specific delay, so the server was not changed.

The user subsequently confirmed LED patterns, Wi-Fi startup and WPA, and
accepted all section 4 transport tasks for now. Task 4.3 is accepted by the user
rather than independently verified for every on-device callback/error case.
Together with captured boot logs and observed controller output, this also
completes task 5.3.

Final user confirmation on 2026-09-28: 2.2 (full invalid-config fatal path),
5.2 (external `/QUIT`), 6.1 (end-to-end telnet acceptance), and 6.2 (cold-boot
acceptance) succeeded. All 19 tasks are complete based on the recorded device
checks, local checks and user acceptance. The original manual checklist is
retained below for reference.

1. Reset/power-cycle and observe one LED blink, two blinks, then steady on.
2. Join PICO MUD using MultiUserDungeon, confirm DHCP provides a client address;
   forget/rejoin with a wrong password and confirm association is refused.
3. Run `telnet 192.168.4.1 8888`. Check welcome and prompt, blank input,
   `/look` → unknown command, and `/QUIT` → goodbye/disconnect.
4. Use several sessions, check the seventh is refused, reconnect after closing
   one, and check an abruptly closed or non-reading client does not stall others.
5. Check idle expiry (temporarily lower IDLE_TIMEOUT and restore it afterwards).
6. Confirm port 80 is closed; no captive portal appears.
7. Observe the fatal three-blink repeating pattern after an invalid config,
   capture the serial traceback, restore the config and reset.

The initial reported association failure occurred while diagnostic cleanup
had switched the AP off. Serial inspection confirmed `AP active: False`;
normal boot was then restarted and logged successfully. The user then confirmed
both Wi-Fi association and external telnet welcome delivery.

## Review

Reviewed correctness, MVC boundaries, input/output bounds and error isolation.
Fixed MicroPython-specific buffer deletion and missing errno constant discovered
on-device. Credentials are the intentionally public defaults; neither passwords
nor input lines are logged. There is no evaluator, database access, HTTP service
or runtime dependency added. Final hardware acceptance was confirmed by the
user, who requested archiving the completed change.

# Documentation for add-core-boot-telnet

- `verification.md`: checks performed, hardware details and the remaining
  user-run Wi-Fi/telnet checklist.
- `mvc-boundaries.md`: utility, controller, view and future model ownership;
  explains how room and item changes share one dirty save unit.
- `micropython-network-wlan.md`: AP setup on rp2, `WLAN.config` params, and
  the WPA2 security constant to verify.
- `micropython-sockets-poll.md`: non-blocking sockets, short writes, why not
  to use `sendall`, poll usage, and MicroPython quirks (`decode`,
  `print_exception`).
- `telnet-protocol.md`: IAC bytes, option negotiation, line endings, and the
  parser state machine.
- Reference implementation: `openspec/reference-project/main.py` (AP + LED)
  and `server.py` (poll loop).
- Project outline: `openspec/PROJECT_OUTLINE.md` (Architecture, Configuration, Telnet
  handling, LED status, Error handling, Networking scope).

Deploy / inspect:
Upload the contents of `target/`, preserving the nested `modules/`,
`controllers/` and `views/` packages beside root-level `config.py` and
`main.py`. Future model packages use the same layout.

```sh
uvx mpremote connect list
uvx mpremote connect /dev/cu.usbmodem2101 fs cp -r target/config.py target/modules target/controllers target/views target/main.py :
uvx mpremote connect /dev/cu.usbmodem2101 reset
uvx mpremote connect /dev/cu.usbmodem2101 repl
telnet 192.168.4.1 8888      # after joining the "PICO MUD" wifi
```

These USB commands were used with the connected Pico 2 W running MicroPython
1.29.0. Replace the port if `connect list` reports a different one. If
`mpremote` is already installed, omit `uvx`. CLI copy/reset behavior reference:
https://github.com/micropython/micropython/blob/master/docs/reference/mpremote.rst
(retrieved with Context7 on 2026-09-28).

Serial REPL attachment does not require switching Wi-Fi. Commands such as
`exec`, `run` and file operations can interrupt/reset the running application;
reset afterwards to resume the hotspot and server. Serial output is not a
persistent log: attach before a reset to capture boot output.

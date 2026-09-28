---
title: "Telnet protocol bytes needed by the PICO MUD server"
source: "RFC 854 (Telnet Protocol Specification), RFC 855 (Option Specification), RFC 857 (Echo)"
created: 2026-09-27
description: "IAC command bytes, option negotiation and line ending rules for input filtering"
tags:
  - "reference"
---

# Telnet essentials (RFC 854/855)

| Name | Byte | Meaning |
|---|---|---|
| IAC | 255 | Interpret As Command: next byte is a command |
| DONT | 254 | followed by 1 option byte |
| DO | 253 | followed by 1 option byte |
| WONT | 252 | followed by 1 option byte |
| WILL | 251 | followed by 1 option byte |
| SB | 250 | start subnegotiation: `IAC SB <opt> ... IAC SE` |
| GA | 249 | go ahead (no option byte) |
| EL/EC/AYT/AO/IP/BRK/DM/NOP | 248–241 | single-byte commands (no option byte) |
| SE | 240 | end subnegotiation |

- `IAC IAC` inside data = literal byte 255.
- NVT uses `CR LF` for a newline and `CR NUL` for a carriage return. The
  project's existing line-input spec additionally accepts CR NUL as an input
  line terminator. Track pending CR across receives so CRLF, LF and that
  compatibility form each deliver one line to the controller; ignoring CR
  and NUL would not implement this project's CR NUL behavior.
- Output must use `CR LF`.
- Common options: ECHO = 1, SUPPRESS-GO-AHEAD = 3, NAWS = 31, LINEMODE = 34.
  Later (login change): `IAC WILL ECHO` (255 251 1) makes the client stop
  local echo for password entry, and `IAC WONT ECHO` (255 252 1) turns it
  back on.
- The default macOS/Linux `telnet` client starts in line mode with local
  echo: the server receives whole lines, and backspace is usually handled
  locally. `nc` sends raw lines with LF.

## Parser states used in design.md
`DATA → (255) IAC → (251..254) OPT → consume 1 byte → DATA`
`IAC → (250) SB → ... (255) SB_IAC → (240) DATA`
`IAC → (255) literal 255 → DATA`, `IAC → other → DATA`

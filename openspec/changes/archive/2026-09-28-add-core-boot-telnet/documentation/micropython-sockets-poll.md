---
title: "MicroPython sockets and select.poll for a non-blocking server"
source: "https://github.com/micropython/micropython/blob/master/docs/library/socket.rst ; https://github.com/micropython/micropython/blob/master/docs/library/select.rst"
created: 2026-09-27
description: "Non-blocking socket semantics, short writes, poll usage, and pitfalls for the telnet server"
tags:
  - "tool-context7"
---

# Sockets + poll on MicroPython

## Delivered transport (2026-09-28)

`modules.telnet.TelnetServer(controller, port, max_clients, idle_timeout,
max_line_length)` exposes `start()`, `poll_once()`, `run()` and `stop()`.
Startup binds before the boot controller signals readiness. Callbacks are
`on_connect`, `on_line`, `on_reject`, `on_timeout`, `on_disconnect` and
`on_tick`, with the arguments listed in design Decision 3.

Clients expose `send(text)` and `close(message=None)`. Output is limited to
4096 bytes; close drains without blocking and expires after 1000 ms. Each
poll turn reads at most 256 bytes per ready client, preserving fairness.
Controller ticks occur every 100 ms and garbage collection every 5 seconds,
measured with `ticks_diff`. No model data is accessed by the transport.

The parser retains IAC/subnegotiation and pending-CR state across reads. It
yields complete UTF-8 lines, accepts LF, CRLF and the project's CR NUL
compatibility delimiter, removes whole characters on BS/DEL, and discards
bytes beyond the 2048-byte line budget until a delimiter. Controllers alone
trim whitespace and interpret commands.

On the actual MicroPython 1.29.0 board, bytearray slice deletion raised
`TypeError` and `errno.EWOULDBLOCK` was absent. The implementation replaces
consumed buffer slices and falls back to `errno.EAGAIN`, respectively.
Serial parser, short-write, output-cap and drain-deadline checks passed.
See `verification.md` for the distinction between device and host checks.

## Key facts from the docs
- `socket.send(bytes)`: "Returns number of bytes sent, which may be smaller
  than the length of data ('short write')."
- `socket.sendall(bytes)`: "The behaviour of this method on non-blocking
  sockets is undefined... on MicroPython, it's recommended to use write()
  method instead, which ... will return number of bytes sent on non-blocking
  sockets." → **Do not use sendall** in the telnet server. Use `send`, and
  keep the unsent tail in the client buffer.
- `setblocking(False)` == `settimeout(0)`.
- `settimeout` is not on every port; the portable approach is `select.poll`:
  ```python
  poller = select.poll()
  poller.register(s, select.POLLIN)
  res = poller.poll(1000)  # ms
  ```
- `recv(n)` returning `b""` means the peer closed the connection.
- Non-blocking `recv`/`send` raise `OSError` with `errno.EAGAIN` when they
  would block; treat it as "try later", not as an error.
- `poll.modify(sock, select.POLLIN | select.POLLOUT)` switches the event
  mask; use POLLOUT only while there is pending output.
- `POLLHUP` / `POLLERR` can be reported without being requested; treat them
  as a disconnect.

## Other MicroPython specifics
- `bytes.decode()` has no `errors="ignore"` argument. Validate or strip
  invalid UTF-8 before decoding.
- `sys.print_exception(e)` prints a traceback (there is no
  `traceback` module).
- `os.rename` on FAT is not atomic (it deletes the target first). The Pico uses
  littlefs, where rename is atomic; this matters for the later persistence
  change.

## Pattern from the reference project (openspec/reference-project/server.py)
- `srv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)`, `bind(("0.0.0.0", port))`,
  `listen(n)`, `setblocking(False)`, then register with poll.
- The loop calls `poll.poll(100)`, accepts connections, reads with
  `recv(1024)`, evicts clients past a timeout, and runs `gc.collect()` every
  ~50 ticks.
- Over MAX_CLIENTS → accept and close immediately (we send "server full"
  first).

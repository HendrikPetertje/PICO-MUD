# Implementation References

This change relies on the project's existing OpenSpec requirements and local
implementation rather than external documentation.

- `openspec/specs/player-communication/spec.md` defines notification routing and
  currently requires unsolicited text to reissue a prompt without ANSI.
- `openspec/specs/command-interface/spec.md` requires plain UTF-8 presentation
  with no ANSI or cursor control.
- `target/controllers/notification_controller.py` currently sends transient
  notices directly to a session's transport buffer.
- `target/controllers/session_controller.py` owns response pumping, busy/missed
  indicators, and the point at which a command response reaches a prompt.

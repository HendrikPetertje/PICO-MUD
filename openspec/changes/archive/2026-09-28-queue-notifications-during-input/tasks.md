# Tasks

## 1. Deferred Session Presentation

- [x] 1.1 Add bounded, transient deferred-notification state and enqueue/clear behavior to `Session`; verify each session retains only its configured capacity, preserves retained arrival order, and releases the state on logout or disconnect.
- [x] 1.2 Update `NotificationController` to enqueue eligible transient notifications through the recipient session rather than writing during command entry; verify room messages, emotes, presence notices, pages, shouts, and new-mail notices retain their existing recipients.
- [x] 1.3 Extend the session output pump to emit a completed command response, retained notifications, an overflow notice when needed, and exactly one plain-text prompt in that order; verify a notification generated while a command is being processed appears before its next prompt.

## 2. Bounded Delivery Verification

- [x] 2.1 Add a host-side focused test harness or test module with a fake client that exercises notifications before and during a partial input line; verify no notification bytes are sent before the line terminator and the completed line still reaches command dispatch unchanged.
- [x] 2.2 Cover multiple deferred notifications and queue overflow in the focused tests; verify retained messages preserve arrival order, deferred output has one final prompt, and overflow produces the missed-notifications notice without unbounded growth.
- [x] 2.3 Run the focused test command and a MicroPython-compatible syntax/import check for all modified `target` modules; verify both pass and no ANSI escape sequence is introduced.

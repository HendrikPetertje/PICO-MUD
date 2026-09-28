# Proposal

## Why

Unsolicited chat, emotes, presence updates, and mail notices currently print
immediately while a player is composing a command. This interrupts the terminal
line and can cause the player to lose or accidentally submit their partial
input.

## What Changes

- Defer transient gameplay notifications for a session until its current command
  input has been received and the session is ready to present output again.
- Preserve the existing plain-text telnet experience; do not introduce ANSI
  cursor-control sequences or depend on terminal-specific line restoration.
- Bound deferred notifications in memory and report a concise omission notice
  when a session cannot retain every pending notification.
- Keep routing rules, recipient privacy, and persistent game state unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `player-communication`: Deliver transient notifications at safe prompt
  boundaries so they do not interrupt a player composing input.

## Impact

- Affects per-session presentation and notification delivery in
  `target/controllers/session_controller.py` and
  `target/controllers/notification_controller.py`.
- May adjust the notification renderer in `target/views/game_view.py`.
- Requires focused host-side tests or a reproducible transport-level check for
  deferred chat, emotes, presence, pages, and mail notifications.
- Does not change commands, saved world data, protocol negotiation, or add
  dependencies.

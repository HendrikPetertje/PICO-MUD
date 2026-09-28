# Proposal

## Why

The Pico now provides a working WPA2 hotspot and MVC telnet shell, but players
cannot log in, build or explore a world. Implement the remaining outline as
one coordinated change so account ownership, room permissions, notifications
and persistence use the same models and session rules.

## What Changes

- Add users, rooms, items-in-rooms and mail models with bounded in-memory data,
  numeric identities, model-owned dirty flags and 30-second selective saves.
- Initialize admin user 1 and permanently public, undeletable global room 1;
  load existing data without overwriting it during deployment or boot.
- Support registered login, prompted or inline passwords, guests, one active
  session per user, home references and owner/admin permissions. Passwords use
  the outline's shared-salt SHA-256 representation; masking is optional and is
  not implemented in this change.
- Implement all outlined commands and aliases: exploration, movement, building,
  static item interactions, chat, mail, account management and administration.
- Keep exits within a single owner's property. Item teleports and explicit
  player teleports can cross properties when the destination is accessible.
- Route direct, room and global notifications through controllers using the
  live session collection; no channels or subscription registry.
- Add validation, resource limits, useful command errors, incremental output
  for large listings, and cleanup of references when rooms or users are removed.
- Update telnet contracts from the bootstrap shell to a playable MUD:
  welcome after authentication, real dispatch, and persistence scheduled by
  controller ticks. Transport remains independent of models and game rules.
- Include command grammar, source notes, deployment instructions and a manual
  acceptance walkthrough covering the complete game loop on the Pico.

This includes the full outline, not a subset of gameplay commands. Wi-Fi and
LED behavior stay under the already implemented capabilities. Inventory,
mutable scripted items, arbitrary Python/MOO execution, public registration,
HTTP, channels and automated test suites are outside the outline and this change.

## Capabilities

### New Capabilities

- `world-persistence`: model-owned state, initialization, IDs, dirty saves,
  file validation, failure handling and memory limits.
- `player-sessions`: login, guests, password prompts, duplicate-login replacement
  and transient presence.
- `command-interface`: complete dispatch, argument resolution, permissions,
  help, exploration and bounded presentation.
- `room-building`: navigation, ownership, privacy, rooms, exits and deletion.
- `item-interactions`: room-local items, bounded actions, moves and teleports.
- `player-communication`: chat, private messages and presence notifications.
- `player-mail`: private bounded inboxes, sending, reading and deleting mail.
- `user-administration`: user lifecycle, admin rights, bans, boots and server tools.

### Modified Capabilities

- `telnet-server`: change bootstrap welcome/unknown-command behavior, permit
  controller-scheduled model saves, preserve password input, and deliver large
  responses incrementally through bounded buffers.

## Impact

Primary code areas are `target/models/`, feature controllers and views,
`target/controllers/telnet_controller.py`, `target/main.py`, and narrow
transport changes for bounded output capacity and overlong-line reporting.
`target/config.py` already contains the required limits; validate them and
replace the construction welcome text at implementation time.

Persistent device files become `/data/users.json`, `/data/rooms.json` and
`/data/mail.json`. Items stay nested in rooms. No external runtime dependencies
are needed. Target remains Pico 2 W / MicroPython 1.29.0, with USB checks
separate from user-operated Wi-Fi/telnet acceptance. Planning does not upload
files to the device or change application code.

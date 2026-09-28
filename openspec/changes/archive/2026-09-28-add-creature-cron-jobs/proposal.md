# Proposal

## Why

Items currently provide static scenery and player-triggered interactions only. Creatures need to be recognizable as living room occupants and able to create timed room activity without requiring a wall clock on the Raspberry Pi Pico.

## What Changes

- Add an optional `creature: true` item flag that classifies an item as a creature while preserving the existing item record, ownership, movement, interaction, and teleport behavior.
- Separate room-look output into `Items:` and `Creatures:` sections so creatures do not appear as ordinary items.
- Add up to three persistent, second-based interval cron jobs per item or creature. Each job has a room-local cron id, name, interval, and optional `chat_out` and `emote` messages.
- Run due cron jobs only while at least one live player occupies the item's room. Send an emote before chat when both are configured.
- Add owner/admin commands to classify items as creatures and add, list, edit, and remove an item's cron jobs: `/creature`, `/habbit add`, `/habbit edit`, `/habbit remove`, and `/habbits`.
- Validate cron-job records on load and persist them through the existing nested room-item storage.

## Capabilities

### New Capabilities
- `creature-scheduling`: interval-based execution of active item and creature cron jobs while players occupy their room.

### Modified Capabilities
- `item-interactions`: classify flagged items as creatures in room views while retaining their established item interaction behavior.
- `world-persistence`: persist and validate creature flags and bounded cron-job records inside room items.
- `command-interface`: document cron management commands and their ownership requirements.
- `player-communication`: deliver creature cron emotes and chat through the existing room notification path in a defined order.

## Impact

- Affects nested item records in `/data/rooms.json`, item validation and editing, room rendering, command registration/dispatch, game views, and the existing telnet tick path.
- Adds a configurable per-item cron-job maximum and interval validation constants; no new database, clock source, dependency, or scripting model is introduced.
- Existing items without `creature` or cron-job fields remain ordinary items with no scheduled behavior.

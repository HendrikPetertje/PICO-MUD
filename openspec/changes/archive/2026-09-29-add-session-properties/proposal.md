# Proposal

## Why

Builders need lightweight per-player progression for puzzles, hidden content, and
temporary creature effects without adding permanent player state that outlives a
story or becomes invalid when its rooms and items change.

## What Changes

- Add a transient session-properties model that stores each live player's values
  by content owner and variable name. It is cleared when the player disconnects
  and on server restart, and it never writes a database file or dirties an
  existing persistent model.
- Add bounded number and string variables, conditions, and mutation effects.
  Each player can hold up to six variables for each content owner; numeric values
  range from 0 through 100 and string names and values are limited to 15
  characters.
- Persist optional condition and effect metadata in rooms, items, interactions,
  and cron jobs, retaining compatibility with existing records that omit it.
- Add an idempotent startup migration layer that upgrades older `rooms.json`
  records to the current schema before validation and safely saves only when a
  migration changes data.
- Gate room entry, item/creature visibility, and item actions on configured
  conditions, while allowing owners and admins to bypass access conditions. Keep
  global and personal home rooms permanently public and ungated.
- Apply interaction and occupied-room cron effects to every affected live player
  and present property changes through player inspection and notifications.
- Extend existing room, interaction, and habbit editing commands and add
  `/help programming` so owners and admins can configure and understand the feature.

## Capabilities

### New Capabilities
- `session-properties`: Provide bounded, per-player, per-owner transient
  variables; conditional checks; variable effects; and property inspection.
- `focused-help`: Organize gameplay documentation into concise, permission-aware
  deep-dive help topics.

### Modified Capabilities
- `world-persistence`: Persist and validate optional conditional and variable
  effect metadata in nested room records without persisting live property values.
- `player-sessions`: Clear a player's transient property state when their active
  session ends or is replaced.
- `room-building`: Apply room entry conditions in addition to private-room access
  across movement, teleports, and joining players.
- `item-interactions`: Apply item/action visibility and availability conditions
  and execute an interaction's configured property effect.
- `creature-scheduling`: Apply a due cron job's property effect to each live
  occupant of its room.
- `command-interface`: Provide builder syntax, variable inspection, notifications,
  and help while keeping inaccessible content hidden.

## Impact

- Affected code: a new transient model; dependency wiring; session lifecycle;
  room, item, and habbit controllers; rooms/items validation and mutation;
  command registry and help; game views; and targeted tests.
- Affected data: optional `unlocked_if`, `visible_if`, `available_if`, and
  `set_variable` fields in `rooms.json`; no new persistent data file.
- No external dependencies or manual migration are required. Startup normalizes
  older rooms with empty condition arrays; existing rooms, items, interactions,
  and cron jobs otherwise retain current behavior.

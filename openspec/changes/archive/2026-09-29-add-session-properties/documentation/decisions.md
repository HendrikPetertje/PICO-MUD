# Session Properties Decisions

## Scope and lifetime

- Properties are held only for live sessions and are never persisted.
- A value belongs to a player and the owner of the room/item content that set it:
  `player_user_id -> owner_user_id -> variable_name -> value`.
- Guest sessions also receive properties. Their values are identified by their
  unique live guest session rather than a persistent user id.
- A player may hold at most six variables for each content owner. Values for one
  owner do not consume another owner's six-variable allowance.

## Values and effects

- Variable names are 1-15 character lowercase ASCII identifiers: they begin with
  a letter; then use letters, digits, and single underscores only. They are shown
  to players with underscores rendered as spaces and the first letter capitalized.
- A stored value is either a number from 0 through 100 or a non-empty string of
  at most 15 characters. A numeric effect is a signed delta, with its resulting
  stored value clamped to that range.
- `set_variable: [name, value]` replaces a string value. A numeric value adjusts
  an existing numeric value, or starts from zero when absent, and the result is
  clamped to the range 0 through 100.
- Effects still apply to owners and admins even though they bypass conditions.
- Admins may edit variable metadata in any room under their existing room-edit
  authority, but cannot set a live player's properties directly.

## Schema migration

- A startup migration runs after loading persistent records and before normal
  validation accepts players. It is idempotent and is the single extension point
  for future persisted-schema upgrades.
- This change migrates missing array fields to empty arrays: room `unlocked_if`,
  item `visible_if`, and interaction `available_if`. Existing valid values are
  preserved.
- `set_variable` remains absent when no effect exists because it is a pair, not a
  collection. Cron jobs do not gain a condition array in this change.
- A migration saves only when it made a change. Invalid present values remain
  invalid and halt startup during validation rather than being erased or replaced.

## Builder command forms

- Room conditions use `/room-unlock-rules add|remove <variable> <condition>
  <value>` and `/room-unlock-rules clear`. The command name corrects the
  request's `unlcok` spelling.
- Item visibility uses `/item set <item> visible add|remove <variable>
  <condition> <value>` and `/item set <item> visible clear`.
- Interaction availability uses `/interaction require <item> <action>
  add|remove <variable> <condition> <value>` and `/interaction require <item>
  <action> clear`. Interaction effects use `/interaction set <item> <action>
  <variable> <value>` and `/interaction clear <item> <action>`.
- Cron effects use `/habbit set <item> <cron-id> <variable> <value>` and
  `/habbit clear <item> <cron-id>`. Variable names are unquoted identifiers. A
  quoted value is always a string, including numeric-looking values such as
  `"01"`; an unquoted integer is numeric.

## Conditions and access

- A condition is `[variable_name, "equals" | "more_than" | "less_than", value]`.
- A list of conditions uses AND semantics: every entry must pass.
- `unlocked_if` is on a destination room. Its condition is evaluated for walking,
  teleporting, item teleports, joining a player, and any other route using shared
  room-entry validation. An unavailable destination is not entered; its source
  exit remains visible.
- `visible_if` hides an item or creature and its interactions from players who do
  not pass. `available_if` hides an interaction from players who do not pass.
- Owners of the relevant property and admins always see and may use conditional
  rooms, items, creatures, and interactions.
- Global home and each user's personal home remain public and rule-free. This
  affects room entry only: items and creatures inside a home room can still be
  hidden or conditional.

# Spec Delta

## Purpose

Make the complete outlined command set discoverable, consistently parsed and
permission checked, with readable output within the Pico's buffer limits.

## ADDED Requirements

### Requirement: Complete command dispatch
The system SHALL implement every command family and alias in this change's
`documentation/command-contract.md`. Command words and direction aliases SHALL
be case-insensitive. Gameplay lines without `/` SHALL be room speech; leading
`"` SHALL be speech and leading `:` an emote. Unknown slash commands SHALL try
a permitted item action, otherwise return an unknown-command/help response.
No input SHALL execute arbitrary code. Expected command failures SHALL leave
the connection open and explain the error.

#### Scenario: Speech versus command
- **WHEN** a player sends `hello`, `"hello`, `:waves` and `/n`
- **THEN** the first two speak, the third emotes and the fourth moves north

### Requirement: Argument and target resolution
Named multiword targets SHALL support double-quoted arguments, with escapes
for quote and backslash; final free-text arguments SHALL retain their contents.
Ids SHALL be parsed as positive integers. Item names SHALL resolve only in the
current room; numeric item targets SHALL be room-local. Ambiguous names or
unterminated quotes SHALL produce an error rather than choose arbitrarily.
`here` and direction aliases SHALL resolve before item names for shared verbs.
Room/item numeric addressing SHALL remain available for colliding names.

#### Scenario: Multiword item
- **WHEN** a builder sends `/describe "brass lever" A polished handle.`
- **THEN** the named local item's description becomes `A polished handle.`

#### Scenario: Ambiguous local target
- **WHEN** two local items have the requested name
- **THEN** the command lists their ids and requires an unambiguous target

### Requirement: Permission and visibility rules
Every command SHALL enforce its guest/user/owner/admin permission at execution.
Admins SHALL enter and edit any room, while preserving same-owner exit rules,
room 1 protections and per-owner quotas. Private mail SHALL remain recipient-only
even for admins. Private room details and contents SHALL be hidden from other
users/guests, including indirect discovery through who, items, rooms and examine.

#### Scenario: Private location in who
- **WHEN** a player lists connected users and another user is in an inaccessible
  private room
- **THEN** the other user's presence is visible but their room details are hidden

### Requirement: Help and inspection
`/help [command]` SHALL list available commands and explain syntax, aliases and
permissions. `/look` (`/l`), `/look at`, `/examine` (`/ex`), `/exits`, `/rooms
[user]`, `/items [user]`, `/who` and `/whoami` SHALL implement the outline's
inspection behavior. Player inspection SHALL show identity and presence, not
invent an editable description field absent from the user schema. Item action
names SHALL be public to visitors; detailed flavor/target editing data SHALL
be restricted to the owner/admin.

#### Scenario: Room view
- **WHEN** a player uses `/look`
- **THEN** they see room name, description, exits, items and players, then a prompt
- **AND** a blank line precedes the room name and follows the player list;
  login, movement and teleports use the same spacing

### Requirement: Bounded complete presentation
Views SHALL render plain UTF-8 text with no ANSI or cursor control. Commands
SHALL deliver complete valid output, including maximum-sized help, room and
user listings, incrementally without exceeding the transport's 4096-byte queue
or disconnecting a normally reading client. Only one command response SHALL
be active per session; extra commands during a response SHALL receive bounded
busy handling rather than accumulate an unbounded queue. The final prompt
SHALL appear only after the response is complete.

#### Scenario: Large listing
- **WHEN** permitted `/rooms` output exceeds 4096 encoded bytes
- **THEN** every visible entry is delivered over multiple flushes and the session
  stays connected, with a final prompt after the last entry

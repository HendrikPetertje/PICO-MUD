# command-interface Specification

## Purpose
Make the complete outlined command set discoverable, consistently parsed and
permission checked, with readable output within the Pico's buffer limits.

## Requirements

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
permissions. `/help tutorial` SHALL be available before and after login and
provide a readable, paragraph-based walkthrough of four existing gameplay
workflows: moving, joining players and teleporting; creating and exploring a
room; creating a message-only item action and a teleporting item action; and
classifying a creature and configuring its timed habbits. The walkthrough SHALL
use valid command examples, explain that item portals can target another
owner's public room but not a private room, and distinguish builder-only steps
from actions that guests may perform. Successful post-login welcome guidance
SHALL direct players to `/help tutorial`. Regular `/help` output SHALL preserve
its command syntax reminder and include a blank line after that reminder before
the final prompt. `/look` (`/l`), `/look at`, `/examine` (`/ex`), `/exits`,
`/rooms [user]`, `/items [user]`, `/who` and `/whoami` SHALL implement the
outline's inspection behavior. Room views SHALL show the `Exits:`, `Items:`,
and `Creatures:` headings only when their corresponding collections contain at
least one visible entry. `/habbits <item>` SHALL list cron-job details for an
item or creature. Player inspection SHALL show identity and presence, not
invent an editable description field absent from the user schema. Item action
names and cron-job summaries SHALL be public to visitors; detailed flavor,
target, and cron-output editing data SHALL be restricted to the owner/admin.

#### Scenario: Room view
- **WHEN** a player uses `/look`
- **THEN** they see room name, description, populated exit, ordinary-item, and
  creature sections, and players, then a prompt
- **AND** a section heading is omitted when it has no visible entries
- **AND** ordinary items appear only below `Items:` and items marked
  `creature: true` appear only below `Creatures:`
- **AND** each item or creature is shown as an indented local name followed by
  its bracketed local id, without repeating the room id
- **AND** a blank line precedes the room name and follows the player list;
  login, movement and teleports use the same spacing

#### Scenario: Public tutorial topic
- **WHEN** a guest runs `/help tutorial`
- **THEN** the MUD shows the four gameplay walkthroughs without requiring a
  login or exposing private room or editing data

#### Scenario: Portal tutorial example
- **WHEN** a registered room owner reads the item-action section of
  `/help tutorial`
- **THEN** it shows one action that returns flavor text and another that assigns
  a teleport destination, and explains that another owner's destination must be
  public

#### Scenario: Welcome and regular help spacing
- **WHEN** a player successfully enters the MUD and later runs `/help`
- **THEN** the welcome guidance mentions `/help tutorial` and the regular help
  response has a blank line between its final syntax reminder and the prompt

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

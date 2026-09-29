# Spec Delta

## ADDED Requirements

### Requirement: Variable configuration, inspection, and help
Owners and admins permitted to edit a room SHALL configure optional room,
item/creature, interaction, and habit conditions or property effects through
extensions to the existing room, `/interaction`, and `/habit` command families.
They SHALL be able to replace or clear each optional field. Invalid names,
operators, values, or condition lists SHALL leave the persistent record
unchanged. `/help programming` SHALL be available to all players and explain
owner-scoped temporary values, limits, AND conditions, numeric adjustment,
string replacement, access bypass, interactions, habits, and the supported
builder command forms.
`/look at self` and `/look at <player>` SHALL show the target's visible current
properties. Admins SHALL use the same builder commands and existing room-edit
authority to configure or repair another owner's variable metadata, and no
command SHALL directly set a live player's properties. Variable names SHALL use
the session-properties identifier syntax; quoted builder values SHALL remain
strings, while unquoted integer tokens SHALL be numeric.

#### Scenario: Builder configures a conditional interaction
- **WHEN** a room owner configures an interaction's availability conditions and
  property effect using its documented existing-command extension
- **THEN** valid metadata is stored and invalid input leaves that interaction unchanged

#### Scenario: Programming help is public
- **WHEN** a guest runs `/help programming`
- **THEN** the MUD explains interactions, habits, and variable-gated stories
  without exposing another owner's configured conditions or property values

## MODIFIED Requirements

### Requirement: Help and inspection
`/help [command]` SHALL provide focused help and explain syntax and aliases.
Regular `/help` SHALL be a focused-help menu rather than a full command list.
The focused menu SHALL advertise
`/help tutorial`, `/help user`, `/help movement`, `/help building`, and
`/help programming`. Each focused topic SHALL be available before and after login,
provide introductory paragraphs, and then show its relevant permission-filtered
command list. Tutorial SHALL cover starting concepts, movement, and chat; user
SHALL cover player/account and communication commands; movement SHALL cover exits,
teleports, homes, and joining; building SHALL cover rooms, exits, descriptions,
and items; programming SHALL cover interactions, habits, and variables.
Successful post-login welcome guidance SHALL direct players to `/help tutorial`.
Focused topic command entries SHALL place syntax on one line, aliases and a
description indented below it, and a blank line before the next entry. `/look` (`/l`),
`/look at`, `/examine` (`/ex`), `/exits`,
`/rooms [user]`, `/items [user]`, `/who` and `/whoami` SHALL implement the
outline's inspection behavior. Room views SHALL show the `Exits:`, `Items:`,
and `Creatures:` headings only when their corresponding collections contain at
least one visible entry. `/habits <item>` SHALL list cron-job details for an
item or creature. Player inspection SHALL show identity, presence, and current
properties, not invent an editable description field absent from the user schema.
Item action names and cron-job summaries SHALL be public to visitors; detailed
flavor, target, condition, property-effect, and cron-output editing data SHALL
be restricted to the owner/admin. Inaccessible conditional rooms, items,
creatures, and actions SHALL not leak through any inspection or listing command.

#### Scenario: Conditional content is absent from inspection
- **WHEN** a visitor does not satisfy an item's visibility condition or an
  interaction's availability condition
- **THEN** the corresponding item or action is absent from room, look, examine,
  item-list, interaction-list, and action-resolution output

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

#### Scenario: Focused help topics
- **WHEN** a guest runs `/help tutorial`, `/help user`, `/help movement`,
  `/help building`, or `/help programming`
- **THEN** the MUD shows that topic's introduction and only commands permitted
  to the guest without exposing private room or editing data

#### Scenario: Public tutorial topic
- **WHEN** a guest runs `/help tutorial`
- **THEN** the MUD shows the getting-started introduction and permitted commands
  without requiring a login or exposing private room or editing data

#### Scenario: Portal tutorial example
- **WHEN** a registered room owner reads `/help programming`
- **THEN** it lists interaction commands that create message and portal actions,
  and explains that portals still use destination access rules

#### Scenario: Welcome and regular help spacing
- **WHEN** a player successfully enters the MUD and later runs `/help`
- **THEN** the welcome guidance mentions `/help tutorial` and the regular help
  response has a blank line between its final syntax reminder and the prompt

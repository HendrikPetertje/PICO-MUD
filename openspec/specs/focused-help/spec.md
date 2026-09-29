# focused-help Specification

## Purpose
Provide discoverable, intent-based deep-dive help so players can learn a focused
area of the MUD without scanning the complete command index.

## Requirements

### Requirement: Focused help menu
Regular `/help` SHALL be a focused-help menu rather than a complete command
index. The menu SHALL advertise `/help tutorial`, `/help user`, `/help movement`,
`/help building`, and `/help programming`.

#### Scenario: Regular help advertises deep dives
- **WHEN** a player runs `/help`
- **THEN** the five focused topics appear without a wall of individual commands

### Requirement: Topic introductions and command lists
Each focused topic SHALL be available before and after login, render introductory
paragraphs, then list its relevant commands using the caller's permissions. Each
command entry SHALL show the command syntax on its own line, optional aliases and
a description indented below it, and a blank line before the next entry.
`tutorial` SHALL cover core concepts, movement, and chat. `user` SHALL cover
accounts, player inspection, communication, and mail. `movement` SHALL cover
exits, teleports, homes, and joining players. `building` SHALL cover rooms,
exits, descriptions, and items. `programming` SHALL cover interactions, habits,
and variables, including variable scope, lifetime, conditions, typed values, and
owner/admin condition bypasses.

#### Scenario: Guest sees safe focused help
- **WHEN** a guest runs each focused help topic
- **THEN** every topic's introduction is shown
- **AND** its command list omits user, owner, and admin commands

#### Scenario: Owner sees building commands
- **WHEN** an owner runs `/help building`
- **THEN** the command list includes permitted room and item building commands

#### Scenario: Programming explains variables
- **WHEN** a player runs `/help programming`
- **THEN** the topic explains interaction and habit effects, per-player
  per-owner variable scope, reset on disconnect or restart, AND conditions,
  numeric deltas, string replacement, and quoted numeric-looking strings

### Requirement: Administrator help
The focused-help menu SHALL advertise `/help admin` only to administrators. The
admin topic SHALL explain the impact of world-management actions and list the
administrator's relevant player, world, and server-operation commands. Its
command entries SHALL retain their `[A]` marker.

#### Scenario: Administrator sees management help
- **WHEN** an administrator runs `/help admin`
- **THEN** the MUD shows the administration introduction and administrator-only
  commands marked `[A]`

#### Scenario: Non-admin cannot open management help
- **WHEN** a guest or ordinary user runs `/help admin`
- **THEN** the MUD refuses access without revealing administrator commands

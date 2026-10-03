# Spec Delta

## MODIFIED Requirements

### Requirement: Complete command dispatch
The system SHALL implement every command family and alias in this change's
`documentation/command-contract.md`. Command words and direction aliases SHALL
be case-insensitive. Gameplay lines without `/` SHALL be room speech; leading
ASCII double quote (`"`) or left typographic double quote (`“`) SHALL be speech
and leading `:` an emote. Unknown slash commands SHALL try a permitted item
action, otherwise return an unknown-command/help response. No input SHALL
execute arbitrary code. Expected command failures SHALL leave the connection
open and explain the error.

#### Scenario: Speech versus command
- **WHEN** a player sends `hello`, `"hello`, `“hello`, `:waves` and `/n`
- **THEN** the first three speak, the fourth emotes and the fifth moves north

### Requirement: Argument and target resolution
Named multiword targets SHALL support either ASCII double quotes (`"..."`) or
paired typographic double quotes (`“...”`) as quoted arguments. ASCII-quoted
arguments SHALL retain the existing backslash escapes for ASCII quote and
backslash; typographic quote characters SHALL not create new escape sequences.
Final free-text arguments SHALL retain their contents. Ids SHALL be parsed as
positive integers. Item names SHALL resolve only in the current room; numeric
item targets SHALL be room-local. Ambiguous names or unterminated/mismatched
quoted arguments SHALL produce an error rather than choose arbitrarily. `here`
and direction aliases SHALL resolve before item names for shared verbs. Room/item
numeric addressing SHALL remain available for colliding names.

#### Scenario: Multiword item
- **WHEN** a builder sends `/describe "brass lever" A polished handle.`
- **THEN** the named local item's description becomes `A polished handle.`

#### Scenario: Ambiguous local target
- **WHEN** two local items have the requested name
- **THEN** the command lists their ids and requires an unambiguous target

#### Scenario: Smart-quoted multiword item
- **WHEN** a builder sends `/describe “brass lever” A polished handle.`
- **THEN** the named local item's description becomes `A polished handle.`

#### Scenario: Smart-quoted numeric string
- **WHEN** a builder supplies `“01”` as a quoted value in a builder command
- **THEN** the stored value is the string `01`, not the integer `1`

#### Scenario: Mismatched typographic quotes
- **WHEN** a player sends an argument beginning with `“` that is not closed by `”`
- **THEN** the command reports an unterminated quote error and makes no change

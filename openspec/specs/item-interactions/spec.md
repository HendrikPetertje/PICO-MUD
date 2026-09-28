# item-interactions Specification

## Purpose
Let owners create room-bound scenery and safe, static interactions that can
display flavor text and teleport the acting player without mutable scripting.

## Requirements

### Requirement: Item lifecycle
Owners/admins SHALL create, rename, describe and destroy items in permitted
rooms. Items SHALL belong to their room's owner and have room-local numeric
ids. Players SHALL NOT pick up, carry or take items. Creation and changes SHALL
respect configured name/text and item limits and preserve the room storage model.

#### Scenario: Create in another property
- **WHEN** an ordinary user tries to create an item in someone else's room
- **THEN** it fails without modifying the room

### Requirement: Item movement
`/move <item> to <room_id>` SHALL move an item only between rooms with the same
owner, with permission to edit both. It SHALL prevalidate destination capacity,
remove the original and recreate its name, description and interactions with a
new room-local identity. It SHALL not create a portable inventory. A same-room
move SHALL be rejected without changing the item.

#### Scenario: Successful move
- **WHEN** a builder moves an item between their rooms with space available
- **THEN** it exists only in the destination with a destination-local id and
  rooms.json is dirty

### Requirement: Interaction editing
`/interaction add`, `/interaction teleport`, `/interaction remove` and
`/interactions` SHALL implement bounded action definitions. Action names SHALL
be unique per item, case-insensitive single words, and SHALL never equal any
built-in command name or alias, including mail and direction commands.
Adding an existing action SHALL update its flavor text without consuming an
extra slot. `teleport ... none` SHALL clear a target. Ordinary owners SHALL
only assign accessible targets: their own rooms or other owners' public rooms.

#### Scenario: Reserved action
- **WHEN** a builder tries to add an action named `LOOK` or `n`
- **THEN** it fails and the item is unchanged

### Requirement: Static interaction execution
`/<action> <item>` SHALL display the action's flavor text to the actor and,
when present, attempt a validated teleport of that actor. It SHALL never modify
the item or run code. `/use <item>` SHALL run its single action, list choices
when there are multiple actions, or explain when no actions exist.
`/look at <item>` SHALL list available action names. Guests SHALL interact.

#### Scenario: Cross-property portal
- **WHEN** a guest uses an item targeting another user's public room
- **THEN** flavor text is displayed and the guest moves there with presence
  notifications, without dirtying any model

#### Scenario: Target became private
- **WHEN** an item targets a room that the actor can no longer enter
- **THEN** flavor text is shown, teleport fails with a message, and the actor stays
  in place; admin access still follows the shared movement rule

### Requirement: Creature classification
Owners and admins permitted to edit the current room SHALL use `/creature <item>
[on|off]` to set or clear an item's `creature: true` classification. An item
with `creature: true` SHALL be classified as a creature for room presentation.
It SHALL otherwise retain all item ownership, room-local identity, movement,
inspection, interaction, and teleport behavior. Items without this flag SHALL
remain ordinary items.

#### Scenario: Creature remains interactive
- **WHEN** a visitor looks at or runs an existing interaction on an item marked as a creature
- **THEN** the inspection and interaction behave the same as for an ordinary item

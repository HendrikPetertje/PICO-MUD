# Spec Delta

## ADDED Requirements

### Requirement: Creature classification
Owners and admins permitted to edit the current room SHALL use `/creature <item> [on|off]` to set or clear an item's `creature: true` classification. An item with `creature: true` SHALL be classified as a creature for room presentation. It SHALL otherwise retain all item ownership, room-local identity, movement, inspection, interaction, and teleport behavior. Items without this flag SHALL remain ordinary items.

#### Scenario: Creature remains interactive
- **WHEN** a visitor looks at or runs an existing interaction on an item marked as a creature
- **THEN** the inspection and interaction behave the same as for an ordinary item

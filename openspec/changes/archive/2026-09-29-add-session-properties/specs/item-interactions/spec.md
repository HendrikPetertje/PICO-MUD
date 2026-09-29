# Spec Delta

## MODIFIED Requirements

### Requirement: Static interaction execution
`/<action> <item>` SHALL display the action's flavor text to the actor and,
when present, attempt a validated teleport of that actor. It SHALL never modify
the item or run code. `/use <item>` SHALL run its single available interaction,
list available choices when there are multiple, or explain when none are
available. `/look at <item>` SHALL list available action names when the item has
actions and SHALL omit the `Actions:` heading when it has none. Guests SHALL
interact. An item or creature with unmet optional `visible_if` conditions SHALL
be hidden. An interaction with unmet optional `available_if` conditions SHALL be
hidden and unavailable. The room owner and admins SHALL bypass those visibility
and availability conditions. A successful interaction with `set_variable` SHALL
apply that effect using the current room owner as its property scope before any
optional teleport.

#### Scenario: Hidden creature
- **WHEN** a visitor does not satisfy a creature's `visible_if` conditions
- **THEN** it is omitted from room, look, examine, item-list, and action target
  resolution output while the owner and admins can still see and use it

#### Scenario: Available action grants a property
- **WHEN** a visitor runs an available item action with a property effect
- **THEN** the actor receives the resulting property notification and any
  configured teleport still uses shared destination validation

#### Scenario: Item with no actions
- **WHEN** a player looks at or examines an item with no interactions
- **THEN** its name and description are displayed without an empty `Actions:`
  heading

#### Scenario: Cross-property portal
- **WHEN** a guest uses an item targeting another user's public room
- **THEN** flavor text is displayed and the guest moves there with presence
  notifications, without dirtying any model

#### Scenario: Target became private
- **WHEN** an item targets a room that the actor can no longer enter
- **THEN** flavor text is shown, teleport fails with a message, and the actor
  stays in place; admin access still follows the shared movement rule

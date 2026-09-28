# Spec Delta

## MODIFIED Requirements

### Requirement: Static interaction execution
`/<action> <item>` SHALL display the action's flavor text to the actor and,
when present, attempt a validated teleport of that actor. It SHALL never modify
the item or run code. `/use <item>` SHALL run its single action, list choices
when there are multiple actions, or explain when no actions exist.
`/look at <item>` SHALL list available action names when the item has actions
and SHALL omit the `Actions:` heading when it has none. Guests SHALL interact.

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
- **THEN** flavor text is shown, teleport fails with a message, and the actor stays
  in place; admin access still follows the shared movement rule

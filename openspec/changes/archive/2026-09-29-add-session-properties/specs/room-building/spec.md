# Spec Delta

## MODIFIED Requirements

### Requirement: Movement and teleportation
The system SHALL support `/go <dir>`, slash directions and n/e/s/w/u/d aliases,
the four outlined home/global-home teleport forms, `/home`, `/teleport to <id>`
and `/join <player>`. Locked exits SHALL block everyone. Destination privacy
and an optional destination `unlocked_if` condition SHALL allow the owner and
admins only when not otherwise satisfied. Guests SHALL use public movement/global
home but have no personal home. Explicit teleport SHALL not require an exit.
All routes, including item teleports, SHALL share destination validation. An exit
leading to a conditionally unavailable room SHALL remain visible. Room 1 SHALL
not accept an `unlocked_if` condition and remain accessible as the public global
home. Every user's personal home SHALL remain public and SHALL not accept an
`unlocked_if` condition.

#### Scenario: Property-gated room entry
- **WHEN** a non-owner tries to walk, teleport, join, or use an item portal into
  a room whose `unlocked_if` conditions they do not satisfy
- **THEN** entry fails, their location and presence announcements remain
  unchanged, and an exit to the room remains listed

#### Scenario: Owner bypasses room condition
- **WHEN** the room owner or an admin enters a room whose `unlocked_if` condition
  they do not satisfy
- **THEN** entry succeeds

#### Scenario: Home room remains public
- **WHEN** an owner or admin tries to add an `unlocked_if` condition to global
  home or a personal home, or make a personal home private
- **THEN** the change fails and the home remains reachable
- **AND** conditional items and creatures inside that home remain allowed

#### Scenario: Private destination
- **WHEN** a non-owner attempts to walk, teleport or join into a private room
- **THEN** entry fails and their location and presence announcements remain unchanged

#### Scenario: Administrator entry
- **WHEN** an admin teleports to another user's private room
- **THEN** entry succeeds; a locked exit still cannot be traversed

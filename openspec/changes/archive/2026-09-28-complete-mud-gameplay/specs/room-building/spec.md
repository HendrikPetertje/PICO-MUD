# Spec Delta

## Purpose

Allow players to navigate and build bounded personal properties while keeping
room ownership, private access and the permanent global home consistent.

## ADDED Requirements

### Requirement: Movement and teleportation
The system SHALL support `/go <dir>`, slash directions and n/e/s/w/u/d aliases,
the four outlined home/global-home teleport forms, `/home`, `/teleport to <id>`
and `/join <player>`. Locked exits SHALL block everyone. Destination privacy
SHALL allow the owner and admins only. Guests SHALL use public movement/global
home but have no personal home. Explicit teleport SHALL not require an exit.
All routes, including item teleports, SHALL share destination validation.

#### Scenario: Private destination
- **WHEN** a non-owner attempts to walk, teleport or join into a private room
- **THEN** entry fails and their location and presence announcements remain unchanged

#### Scenario: Administrator entry
- **WHEN** an admin teleports to another user's private room
- **THEN** entry succeeds; a locked exit still cannot be traversed

### Requirement: Same-owner digging
`/dig <dir> <name>` SHALL create a room owned by the source room's owner and
two opposite exits, within that owner's quota. `/dig <dir> to <id>` SHALL link
existing rooms only if both have the same owner and both exit slots are free.
Admins editing another owner's property SHALL retain that ownership. No dig
form SHALL create a cross-owner exit, even for an admin. Failed validation
SHALL create no partial room or exit.

#### Scenario: Link to another owner's public room
- **WHEN** a user or admin tries to dig between differently owned public rooms
- **THEN** the command fails and neither room changes

#### Scenario: Occupied reverse exit
- **WHEN** an existing destination already has the opposite exit occupied
- **THEN** linking fails without replacing either exit

### Requirement: Room and exit editing
Owners/admins SHALL use `/rename here`, `/describe here`, `/private [on|off]`,
exit `/rename`, `/describe`, `/message`, `/lock`, `/unlock` and `/undig`.
`/undig` SHALL remove only the selected source exit; it SHALL not silently
remove a return exit. Toggling privacy on SHALL move non-owner, non-admin
occupants to room 1. Room 1 SHALL reject becoming private or being deleted.

#### Scenario: Private room with visitors
- **WHEN** an owner makes a room private while guests are present
- **THEN** unauthorized visitors move to room 1 and future entry is denied

### Requirement: Personal home
`/sethome` SHALL set the acting registered user's home only to a room they
actually own, even when the user is an admin. Room 1 SHALL remain the global
home when admin user 1 chooses another personal home.

#### Scenario: Admin changes home
- **WHEN** admin user 1 sets another owned room as home
- **THEN** `/home` leads there while global-home commands still lead to room 1

### Requirement: Room deletion and references
`/destroy room <id>` SHALL require ownership or admin permission and reject
room 1 and every current personal home. It SHALL remove the room and its items,
remove incoming exits, clear item teleport targets pointing to it, and relocate
occupants to room 1. The controller SHALL coordinate notifications and models
SHALL mark affected save units dirty.

#### Scenario: Delete a linked room
- **WHEN** a permitted non-home room is destroyed
- **THEN** it and its contents vanish, no exit or interaction targets its id,
  and its occupants receive the global-home room view

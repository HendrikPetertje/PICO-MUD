# Spec Delta

## Purpose

Give administrators bounded account and moderation controls while preserving
the initial admin, global home, ownership and references throughout the world.

## ADDED Requirements

### Requirement: User creation and inspection
Admins SHALL use `/user create <name> <password> [admin]` to create a unique
case-insensitive username, password hash and owned home room within limits.
Creation SHALL validate all parts before publishing either user or room.
`/users` SHALL show id, name, admin/banned flags and home id, never credentials.
`guest` and the generated `guest-N` namespace SHALL be reserved.

#### Scenario: At user capacity
- **WHEN** MAX_USERS accounts exist and an admin creates another
- **THEN** it fails without an orphan user or room

### Requirement: Account rights and password reset
Admins SHALL grant/revoke rights with `/user admin <name> [on|off]`, reset
passwords with `/user password <name> <new>`, and ban/unban with `/user ban`
and `/user unban`. An omitted admin flag SHALL toggle it. Current permissions
SHALL take effect on the next command without relogin. User 1 SHALL remain
admin, unbanned and undeletable. Existing passwords SHALL not be displayed.

#### Scenario: Ban active user
- **WHEN** an admin bans an online user other than user 1
- **THEN** that session is removed and disconnected and subsequent login fails

### Requirement: User removal and referential cleanup
`/user remove <name>` SHALL delete the permitted user, all their rooms/items
and inbox, disconnect their session, move other affected occupants to room 1,
remove incoming exits and item teleport targets, and remove mail authored by
the deleted user from other inboxes. Remaining ids SHALL not refer to that
user or their rooms. Removing user 1 SHALL always fail.

#### Scenario: User with visitors and sent mail
- **WHEN** an admin removes a user who owns occupied rooms and has sent mail
- **THEN** visitors move to room 1, associated data and references are cleaned,
  and each affected save unit becomes dirty

### Requirement: Boot and server utilities
`/boot <player>` SHALL disconnect a live user or guest without banning them.
`/save` SHALL require admin permission and report which dirty files saved,
remained dirty on failure, or needed no write. `/uptime` SHALL be available
to gameplay sessions and report elapsed uptime, free heap, connected count,
user count/limit and room counts against configured limits.

#### Scenario: Clean save
- **WHEN** an admin requests `/save` with no dirty models
- **THEN** the reply reports no writes needed and no file is overwritten

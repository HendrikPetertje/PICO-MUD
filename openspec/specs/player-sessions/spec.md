# player-sessions Specification

## Purpose
Provide registered and guest access to the MUD with one live session per user,
separate password prompts, consistent identity and transient presence.

## Requirements

### Requirement: Login and prompted password
`/connect <name> <password>` and `/login <name> <password>` SHALL authenticate
against the configured-salt SHA-256 hash. Omitting the password SHALL prompt
for it on the next line; that line is password data rather than a command and
SHALL preserve case and whitespace. Visible inline passwords and visible prompt
input SHALL be accepted; masking is not required. Empty or over-250-character
passwords SHALL be refused. Before login, only connect/login, help and quit
SHALL be available. Unknown users, bad passwords and banned users SHALL NOT
enter the world or displace an existing session.

#### Scenario: Prompted login
- **WHEN** a client submits `/connect adam` and then the correct password
- **THEN** it authenticates as Adam and enters room 1 with welcome and instructions

#### Scenario: Failed replacement attempt
- **WHEN** another client submits Adam's name and an incorrect password
- **THEN** authentication fails while Adam's current session remains connected

### Requirement: Password storage and change
Passwords SHALL be stored only as the hex digest of SHA-256 over UTF-8
`PASSWORD_SALT + password`, matching the outline. `/password <old> <new>` SHALL
change only the authenticated user's password after verifying the old value.
Passwords and hashes SHALL NOT appear in logs, look/examine, user listings or
mail. Config credentials SHALL seed only first boot, not overwrite existing users.

#### Scenario: Password change survives restart
- **WHEN** a user changes their password and the users model is saved
- **THEN** the new password authenticates after restart and the old one fails

### Requirement: Guest sessions
`/connect guest` SHALL create a unique live `guest-N` identity without a database
record, mailbox or personal home. Guests SHALL explore accessible rooms, use
items and communicate, but not build, edit, administer or use mail. Guest names
SHALL not collide with registered usernames. Reconnects need not retain identity.

#### Scenario: Guest permissions
- **WHEN** a guest looks, moves, reads an item and then tries `/create sign`
- **THEN** allowed actions work and creation is refused without dirtying models

### Requirement: Single login and cleanup
Only one live session SHALL represent a registered user. Successful duplicate
login SHALL remove the old session from gameplay immediately, notify and close
its connection, and enter the new session in room 1. A delayed disconnect
callback for the old connection SHALL NOT remove the replacement. Disconnect,
boot, ban and timeout SHALL release presence and queued responses exactly once,
and SHALL discard that session's transient properties.

#### Scenario: Reconnect clears properties
- **WHEN** a user disconnects after receiving a property and then logs in again
- **THEN** their new session has no properties from the previous session

#### Scenario: Duplicate login
- **WHEN** Adam successfully logs in from a second connection
- **THEN** the old connection stops acting as Adam and is disconnected
- **AND** its later cleanup leaves the new session active

### Requirement: Stable world entry and account switching
After login or guest entry, the system SHALL display WELCOME_TEXT, navigation
instructions and room 1. `/connect` during an active session SHALL report that
the player must disconnect to change identity. The session controller SHALL
hold identity/current room in memory only. Notifications SHALL not interrupt
the pre-login password exchange with a gameplay prompt.

#### Scenario: Restart clears presence
- **WHEN** the server restarts and a returning user logs in
- **THEN** they enter room 1, regardless of their previous session location

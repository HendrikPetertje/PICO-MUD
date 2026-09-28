# world-persistence Specification

## Purpose
Preserve the MUD's users, rooms, nested items and mail across restarts while
keeping presence transient and writes bounded on the Pico's flash storage.

## Requirements

### Requirement: Authoritative models and file shapes
The system SHALL store users as an array in `/data/users.json`, rooms with
nested items as an array in `/data/rooms.json`, and inbox arrays keyed by user
id in `/data/mail.json`. Separate users, rooms, items and mail models SHALL own
operations on this shared state. Items SHALL share room storage and its dirty
flag, without an items file or duplicate database. Sessions SHALL NOT persist.

#### Scenario: Item edit uses room storage
- **WHEN** a permitted player edits an item's description
- **THEN** the room's nested item changes and only the rooms save unit is dirty
- **AND** reconnecting or walking does not dirty any save unit

### Requirement: Numeric identities
User and room ids and all stored references SHALL be positive integers, not
booleans or numeric strings. Item ids SHALL be unique within their room and
addressed together with a room id. JSON inbox object keys SHALL be canonical
decimal strings on disk and converted to integer keys in memory because JSON
object keys cannot be numbers. Referenced records SHALL be validated on load.

#### Scenario: Mail round trip
- **WHEN** an inbox belonging to user 2 is saved and loaded
- **THEN** its disk key is `"2"`, its in-memory key is integer 2, and sender ids
  inside messages remain numeric

### Requirement: First boot and global home
With no database files, the system SHALL create admin user 1 from config and
public room 1 owned by that user, with a name, description and empty exits/items.
The admin's initial personal home SHALL be room 1; other users SHALL receive
their own new home. Room 1 SHALL always exist and remain public, independently
of later personal-home changes. Initialization SHALL be saved before accepting
players. Existing valid records SHALL survive restart and code deployment.

#### Scenario: Fresh world
- **WHEN** the application starts without database files
- **THEN** user 1, room 1 and an empty mail database are created and saved
- **AND** a subsequent restart loads them rather than resetting passwords or rooms

### Requirement: Boot validation and recovery boundary
The system SHALL validate loaded types, ids, ownership, limits and references
before accepting players. Malformed files or incomplete users/rooms pairs SHALL
produce a serial diagnostic and fatal startup state without overwriting the
files. Missing mail alongside valid users/rooms SHALL initialize empty inboxes.
Stale temporary files SHALL NOT replace an existing valid primary file.

#### Scenario: Corrupt rooms file
- **WHEN** rooms.json is malformed or refers to a nonexistent owner
- **THEN** startup stops with a diagnostic and the existing files are preserved

### Requirement: Dirty periodic persistence
Successful persistent mutations SHALL mark the affected model dirty. Reads,
failed validation and unchanged assignments SHALL NOT cause writes. Every
SAVE_INTERVAL seconds (default 30), controller scheduling SHALL ask each dirty
file owner to save. `/save` SHALL request the same check immediately. Serialization
SHALL stream to a temporary file and replace the primary only after successful
close; flags SHALL clear only on success. A failed file SHALL remain dirty for
retry, report the failure and not prevent attempts to save other dirty files.

#### Scenario: Selective write and retry
- **WHEN** only rooms are dirty and their save fails
- **THEN** users and mail are not rewritten, the rooms flag remains set and
  the next interval retries

#### Scenario: Idle world
- **WHEN** no persistent changes occur through several intervals
- **THEN** no database file is rewritten

### Requirement: Configured limits and memory admission
The system SHALL enforce MAX_USERS=15, MAX_ROOMS_PER_USER=10 (including home),
MAX_ITEMS_PER_ROOM=5, MAX_INTERACTIONS_PER_ITEM=2, MAX_MAILS=10,
MAX_NAME_LENGTH=60, MAX_DESCRIPTION_LENGTH=600 for room/item/exit descriptions
and MAX_TEXT_LENGTH=250 for activation/flavor text, chat and mail messages
using config values. The description limit SHALL apply to edits and
loaded data, and count Unicode characters rather than UTF-8 bytes. Before growing
persistent state, it SHALL collect garbage and reject the operation if free
heap is below MIN_FREE_MEMORY (32768 bytes). Rejected operations SHALL preserve
existing data. Limits also apply to admins. Memory figures SHALL be observable
through `/uptime`; configured maxima are ceilings, not guaranteed capacity.

#### Scenario: Destination room is full
- **WHEN** an item move would exceed the target room's item limit
- **THEN** the move fails and the original item remains intact

#### Scenario: Low memory
- **WHEN** a create, text expansion or mail operation is attempted below the
  configured free-memory threshold after collection
- **THEN** it is rejected with a useful message and existing records are unchanged

#### Scenario: Longer descriptions survive reload
- **WHEN** a player saves a room, item or exit description of 600 Unicode characters
- **THEN** it is accepted and loads intact after restart
- **AND** a 601-character replacement is rejected without changing the existing description

#### Scenario: Other text limits remain separate
- **WHEN** a player submits 251 characters of chat, mail body, exit activation
  text or interaction flavor text
- **THEN** the operation is rejected despite the longer room/item description limit

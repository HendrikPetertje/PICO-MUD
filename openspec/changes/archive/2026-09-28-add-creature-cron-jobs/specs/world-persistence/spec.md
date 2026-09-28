# Spec Delta

## MODIFIED Requirements

### Requirement: Authoritative models and file shapes
The system SHALL store users as an array in `/data/users.json`, rooms with nested items as an array in `/data/rooms.json`, and inbox arrays keyed by user id in `/data/mail.json`. Separate users, rooms, items and mail models SHALL own operations on this shared state. Items SHALL share room storage and its dirty flag, without an items file or duplicate database. An item MAY persist `creature: true` and a bounded list of cron-job definitions; both remain part of its nested room record. Sessions and elapsed cron-job scheduling state SHALL NOT persist.

#### Scenario: Creature cron configuration round trip
- **WHEN** an owner saves an item with `creature: true` and configured cron jobs
- **THEN** the nested item data survives restart while the first post-restart execution waits for a new elapsed interval

#### Scenario: Item edit uses room storage
- **WHEN** a permitted player edits an item's description
- **THEN** the room's nested item changes and only the rooms save unit is dirty
- **AND** reconnecting or walking does not dirty any save unit

### Requirement: Boot validation and recovery boundary
The system SHALL validate loaded types, ids, ownership, limits and references before accepting players. Malformed files or incomplete users/rooms pairs SHALL produce a serial diagnostic and fatal startup state without overwriting the files. Missing mail alongside valid users/rooms SHALL initialize empty inboxes. Stale temporary files SHALL NOT replace an existing valid primary file. A creature flag, when present, SHALL be boolean and true. Cron-job records SHALL have unique positive numeric ids, valid bounded names and intervals, and valid optional output text.

#### Scenario: Invalid cron record stops boot
- **WHEN** a stored item contains a cron job with a duplicate id, non-positive interval, or invalid field type
- **THEN** startup stops with a diagnostic and preserves the existing files

#### Scenario: Corrupt rooms file
- **WHEN** rooms.json is malformed or refers to a nonexistent owner
- **THEN** startup stops with a diagnostic and the existing files are preserved

### Requirement: Configured limits and memory admission
The system SHALL enforce MAX_USERS=15, MAX_ROOMS_PER_USER=10 (including home), MAX_ITEMS_PER_ROOM=5, MAX_INTERACTIONS_PER_ITEM=2, MAX_CRON_JOBS_PER_ITEM=3, MAX_MAILS=10, MAX_NAME_LENGTH=60, MAX_DESCRIPTION_LENGTH=600 for room/item/exit descriptions and MAX_TEXT_LENGTH=250 for activation/flavor text, chat, emote and mail messages using config values. The description limit SHALL apply to edits and loaded data, and count Unicode characters rather than UTF-8 bytes. Before growing persistent state, it SHALL collect garbage and reject the operation if free heap is below MIN_FREE_MEMORY (32768 bytes). Rejected operations SHALL preserve existing data. Limits also apply to admins. Memory figures SHALL be observable through `/uptime`; configured maxima are ceilings, not guaranteed capacity.

#### Scenario: Cron output text is bounded
- **WHEN** a builder submits chat or emote output longer than MAX_TEXT_LENGTH
- **THEN** the operation is rejected without changing the cron job

#### Scenario: Destination room is full
- **WHEN** an item move would exceed the target room's item limit
- **THEN** the move fails and the original item remains intact

#### Scenario: Low memory
- **WHEN** a create, text expansion or mail operation is attempted below the configured free-memory threshold after collection
- **THEN** it is rejected with a useful message and existing records are unchanged

#### Scenario: Longer descriptions survive reload
- **WHEN** a player saves a room, item or exit description of 600 Unicode characters
- **THEN** it is accepted and loads intact after restart
- **AND** a 601-character replacement is rejected without changing the existing description

#### Scenario: Other text limits remain separate
- **WHEN** a player submits 251 characters of chat, mail body, exit activation text or interaction flavor text
- **THEN** it is rejected despite the longer room/item description limit

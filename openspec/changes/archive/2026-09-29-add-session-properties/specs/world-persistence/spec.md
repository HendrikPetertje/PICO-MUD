# Spec Delta

## MODIFIED Requirements

### Requirement: Authoritative models and file shapes
The system SHALL store users as an array in `/data/users.json`, rooms with
nested items as an array in `/data/rooms.json`, and inbox arrays keyed by user
id in `/data/mail.json`. Separate users, rooms, items and mail models SHALL own
operations on this shared state. Items SHALL share room storage and its dirty
flag, without an items file or duplicate database. An item MAY persist
`creature: true` and a bounded list of cron-job definitions; both remain part of
its nested room record. Every normalized room SHALL contain `unlocked_if`, every
normalized item SHALL contain `visible_if`, and every normalized interaction
SHALL contain `available_if`; items/interactions/cron jobs MAY persist
`set_variable`. Sessions, elapsed cron-job scheduling state, and live session
properties SHALL NOT persist.

#### Scenario: Conditional metadata round trip
- **WHEN** an owner saves rooms containing valid condition and property-effect
  metadata
- **THEN** that metadata survives restart while live player property values do not

#### Scenario: Item edit uses room storage
- **WHEN** a permitted player edits an item's description
- **THEN** the room's nested item changes and only the rooms save unit is dirty
- **AND** reconnecting or walking does not dirty any save unit

#### Scenario: Creature cron configuration round trip
- **WHEN** an owner saves an item with `creature: true` and configured cron jobs
- **THEN** the nested item data survives restart while the first post-restart
  execution waits for a new elapsed interval

## ADDED Requirements

### Requirement: Startup schema migration
The system SHALL run an idempotent persistent-schema migration after loading
records and before accepting players. This migration SHALL add an empty
`unlocked_if` array to every room missing it, an empty `visible_if` array to
every item missing it, and an empty `available_if` array to every interaction
missing it. It SHALL preserve present valid values, save rooms only when it made
a change, and validate the migrated data before accepting players. Missing
`set_variable` fields SHALL remain absent. A present invalid field SHALL halt
startup under normal validation and SHALL NOT be erased or replaced by migration.

#### Scenario: Older rooms gain empty condition arrays
- **WHEN** a valid existing rooms file omits the new condition arrays
- **THEN** startup adds empty arrays at every required level, saves the migrated
  rooms file, and accepts players only after validation succeeds

#### Scenario: Repeated migration stays clean
- **WHEN** the server starts with an already migrated valid rooms file
- **THEN** the migration makes no persistent change and does not rewrite rooms

### Requirement: Outline schema documentation
The project outline SHALL document the normalized `rooms.json` schema and every
persisted session-property field introduced by this change, including empty
condition arrays and optional property effects. It SHALL be updated in the same
patch as the migration and validation changes so its data examples and command
reference match the implemented behavior.

#### Scenario: Implementation patch updates the outline
- **WHEN** session-property persistence support is added or changed
- **THEN** `openspec/PROJECT_OUTLINE.md` documents the resulting `rooms.json`
  fields, validation semantics, and builder command forms in that same patch

## MODIFIED Requirements

### Requirement: Boot validation and recovery boundary
The system SHALL validate loaded types, ids, ownership, limits and references
before accepting players. Malformed files or incomplete users/rooms pairs SHALL
produce a serial diagnostic and fatal startup state without overwriting the
files. Missing mail alongside valid users/rooms SHALL initialize empty inboxes.
Stale temporary files SHALL NOT replace an existing valid primary file. A
creature flag, when present, SHALL be boolean and true. Cron-job records SHALL
have unique positive numeric ids, valid bounded names and intervals, and valid
optional output text. Optional condition lists and property effects SHALL have
valid bounded names, operators, value types, and values.

#### Scenario: Invalid conditional metadata stops boot
- **WHEN** a stored condition has an unknown operator or a property effect has
  an empty name, an out-of-range number, or an overlong string
- **THEN** startup stops with a diagnostic and preserves the existing files

#### Scenario: Corrupt rooms file
- **WHEN** rooms.json is malformed or refers to a nonexistent owner
- **THEN** startup stops with a diagnostic and the existing files are preserved

#### Scenario: Invalid cron record stops boot
- **WHEN** a stored item contains a cron job with a duplicate id, non-positive
  interval, or invalid field type
- **THEN** startup stops with a diagnostic and preserves the existing files

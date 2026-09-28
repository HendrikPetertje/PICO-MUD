# creature-scheduling Specification

## Purpose

Provide bounded, interval-based room activity for items and creatures without a wall clock or a separate persistent scheduler.

## Requirements

### Requirement: Occupancy-gated interval cron jobs
An item or creature SHALL define at most three cron jobs. Each cron job SHALL have a positive room-local numeric id, a non-empty name, a positive interval in whole seconds, and optional `emote` and `chat_out` text values. A cron job without output SHALL remain valid and silent. A cron job SHALL run only after its interval has elapsed and only while at least one live gameplay session occupies the item's room. It SHALL not run or accumulate missed executions while the room is empty.

#### Scenario: Empty room pauses a due job
- **WHEN** a cron job becomes due while no live gameplay session occupies its room
- **THEN** it emits no message and does not run until a later due interval while the room is occupied

#### Scenario: Occupied room runs a due job
- **WHEN** a live gameplay session occupies the item's room when a cron-job interval elapses
- **THEN** the job executes once and delivers its configured output to that room

### Requirement: Cron job output order
When a due cron job has an `emote`, the system SHALL send it to the item's room as an emote attributed to the item name. When it has `chat_out`, the system SHALL send it to the same room as speech attributed to the item name. When both values exist, the emote SHALL be delivered before the chat message. A cron job with neither value SHALL execute silently.

#### Scenario: Emote precedes chat
- **WHEN** an occupied room contains a due cron job with both `emote` and `chat_out`
- **THEN** occupants receive the item emote before the item chat message

### Requirement: Cron job management
Owners and admins permitted to edit the current room SHALL manage the current room's item or creature cron jobs with `/habbit add <item> <interval-seconds> <name>`, `/habbit edit <item> <cron-id> interval <seconds>`, `/habbit edit <item> <cron-id> name <name>`, `/habbit edit <item> <cron-id> <chat|emote> <on|off> [text]`, `/habbit remove <item> <cron-id>`, and `/habbits <item>`. Additions and changes SHALL enforce configured name and text limits, reject non-positive intervals and unknown cron ids, and preserve the item on failed validation. Turning chat or emote off SHALL clear the selected optional output; turning it on SHALL require text.

#### Scenario: Owner configures and inspects a job
- **WHEN** an owner adds a cron job to an item and configures its emote and chat output
- **THEN** `/habbits <item>` lists its id, name, interval, and configured output values

#### Scenario: Fourth job is rejected
- **WHEN** a builder adds a fourth cron job to an item that already has three
- **THEN** the command fails and the three existing jobs remain unchanged

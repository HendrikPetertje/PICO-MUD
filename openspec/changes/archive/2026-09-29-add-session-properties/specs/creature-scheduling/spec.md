# Spec Delta

## MODIFIED Requirements

### Requirement: Occupancy-gated interval cron jobs
An item or creature SHALL define at most three cron jobs. Each cron job SHALL have a positive room-local numeric id, a non-empty name, a positive interval in whole seconds, and optional `emote`, `chat_out`, and `set_variable` values. A cron job without output or a property effect SHALL remain valid and silent. A cron job SHALL run only after its interval has elapsed and only while at least one live gameplay session occupies the item's room. It SHALL not run or accumulate missed executions while the room is empty. When it has `set_variable`, it SHALL apply the effect to every live occupant using the room owner as the property scope.

#### Scenario: Occupied room grants a property
- **WHEN** a due cron job with a property effect runs in a room occupied by two
  players
- **THEN** each occupant receives the effect and its resulting-property notification

#### Scenario: Empty room pauses a due job
- **WHEN** a cron job becomes due while no live gameplay session occupies its room
- **THEN** it emits no message and does not run until a later due interval while
  the room is occupied

#### Scenario: Occupied room runs a due job
- **WHEN** a live gameplay session occupies the item's room when a cron-job
  interval elapses
- **THEN** the job executes once and delivers its configured output to that room

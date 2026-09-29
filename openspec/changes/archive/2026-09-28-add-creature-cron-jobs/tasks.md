# Tasks

## 1. Persisted Item Data

- [x] 1.1 Add `MAX_CRON_JOBS_PER_ITEM = 3` to configuration and startup validation; verify invalid configuration values prevent startup before the server accepts clients.
- [x] 1.2 Extend item creation, replacement, movement, and load validation for optional `creature` and `cron_jobs` fields, including bounded unique cron ids, intervals, names, optional output text, and backward-compatible absent fields; verify valid saved records reload and invalid records halt without overwriting `rooms.json`.
- [x] 1.3 Implement item-model operations to add, update, remove, and list cron jobs while preserving data on failed validation; verify a fourth job, unknown id, non-positive interval, and oversized text are rejected without mutation while a silent job remains valid.

## 2. Builder Commands And Views

- [x] 2.1 Register `/creature`, `/habit add`, `/habit edit`, `/habit remove`, and `/habits` with help text and route them through owner/admin item-edit permission checks; verify guests and non-owners cannot mutate creatures or jobs while permitted builders can.
- [x] 2.2 Parse habit edit interval, name, and chat/emote on/off forms and display stable cron id, name, interval, and authorized output details in `/habits`; verify silent jobs remain valid and owner/admin versus visitor visibility matches the specification.
- [x] 2.3 Split `/look` room rendering into `Items:` and `Creatures:` based on `creature: true` without changing lookup, inspection, interactions, or teleports; verify a creature appears only under `Creatures:` and remains usable via `/look at`, `/use`, and action verbs.

## 3. Runtime Scheduling

- [x] 3.1 Add a volatile cron scheduler to the application tick path that uses monotonic elapsed milliseconds and schedules a fresh interval after boot; verify elapsed runtime state is not written to `rooms.json` and jobs do not fire immediately after restart.
- [x] 3.2 Gate scheduling on live occupancy of the item's current room, clear inactive-room progress, and reconcile removed or moved item/job keys; verify empty rooms do not emit or accumulate executions and moved/deleted jobs leave no stale execution.
- [x] 3.3 Deliver due output through room notifications using the existing game speech/emote formatting, sending emote before chat and no more than one execution per job per tick; verify only current room occupants receive output in the required order.

## 4. Integration Verification

- [x] 4.1 Exercise a persisted creature and ordinary-item cron job through add, output edits, `/habits`, save/reload, occupied execution, empty-room pause, and removal; verify no unrelated item interaction, movement, or teleport behavior regresses.
- [x] 4.2 Run the available host-side validation or compile/import checks and a Pico deployment smoke test; verify startup, `/help`, `/look`, habit commands, and scheduled notifications work without transport queue or prompt corruption.

# Design

## Context

See `proposal.md` for motivation. Items are nested in room records, and the items model owns their validation and persistent mutations. The telnet server supplies a monotonic millisecond tick; `PersistenceController.tick()` accumulates elapsed time, while `TelnetController` owns live sessions and room notifications. The device has no real-time clock.

## Goals / Non-Goals

**Goals:**
- Persist creature classification and bounded cron-job definitions with their existing nested item.
- Schedule interval work from monotonic elapsed time without wall-clock or calendar syntax.
- Deliver automated output through existing room-scoped notification formatting and prompt handling.
- Keep inactive rooms quiet and avoid catch-up bursts after they become occupied.

**Non-Goals:**
- General scripting, arbitrary execution, portable inventories, creature AI, combat, pathfinding, or creature movement.
- Calendar cron expressions, clock synchronization, and durable last-run timestamps.
- Changing interaction or teleport semantics for creature-flagged items.

## Decisions

### Preserve a single item model

Add optional `creature` and `cron_jobs` fields to existing item dictionaries rather than introduce creature records or another storage file. This preserves room-local ids, owner permissions, move behavior, room persistence, and item action handling.

Alternative considered: a separate creature model and file. Rejected because it duplicates references, persistence, and rendering lookup paths on a constrained device.

### Schedule in volatile runtime state

Keep each cron job's last-run/elapsed state in a scheduler owned by the live application controller, keyed by room and item identity plus cron id. Feed it elapsed milliseconds from the existing monotonic tick. On restart, jobs begin a fresh interval rather than firing immediately or replaying downtime.

Alternative considered: persist absolute timestamps. Rejected because the Pico lacks a dependable wall clock and persistent timing would create undefined downtime behavior.

### Gate and reset work on room occupancy

On each scheduler tick, identify rooms with live gameplay sessions. Only advance eligible jobs for occupied rooms; when a room is empty, reset or discard its elapsed progress so it cannot accrue executions. Process at most one run per job per tick, avoiding burst delivery when the loop is delayed.

Alternative considered: always schedule and suppress output in empty rooms. Rejected because it makes job timing depend on unobserved activity and can create catch-up ambiguity.

### Reuse room notification and message views

Route a cron emote and chat through room notifications using the existing speech/emote view formatting, passing the item name as speaker. Emit emote first, then chat. The notification controller already filters live and writable sessions and restores prompts for unsolicited output.

Alternative considered: send directly to sockets from the scheduler. Rejected because it would bypass established session eligibility and transport behavior.

### Manage cron jobs through explicit bounded commands

Extend command registration and item editing with the agreed `/habbit` subcommands plus `/habbits`. Validate creation and updates in the items model. Use next available room-local cron ids, preserving ids of unrelated jobs.

Alternative considered: encode cron data in interaction text. Rejected because it conflates player-triggered behavior with scheduled output and prevents clear validation.

## Risks / Trade-offs

- [Tick stalls can delay jobs] → Calculate elapsed time with `time.ticks_diff`, cap execution at one run per due job per tick, and do not replay backlog.
- [Runtime schedule keys can become stale after item moves, removals, or edits] → Reconcile scheduled entries against current nested item records each tick and discard missing keys.
- [Additional nested data consumes scarce Pico heap] → Cap jobs at three per item, retain current text limits, and use existing memory admission before persistent growth.
- [Existing saved items lack new fields] → Treat absent `creature` as false and absent `cron_jobs` as an empty list while strictly validating fields that are present.

## Migration Plan

1. Deploy code that accepts existing item records with absent creature and cron fields.
2. Validate newly stored cron records during boot before serving users.
3. Roll back by deploying the prior code only after removing newly stored cron fields from `rooms.json`; prior validation does not recognize them.

# Design

## Context

See `proposal.md` for motivation and the delta specs for required behavior. The
current application has persistent users, rooms, nested items, and mail models;
it stores session identity and location in `Session`; and its room, item, and
habit controllers already centralize movement, interaction execution, and
occupied-room cron delivery. Those paths must share property-aware access checks
without adding a database file or changing old saved records.

## Goals / Non-Goals

**Goals:**

- Keep per-player story state bounded, owner-scoped, and wholly in memory.
- Make every condition and effect path use one validation and evaluation policy.
- Preserve existing behavior when optional room metadata is absent.
- Prevent information leaks from hidden items, creatures, and unavailable actions.
- Establish a safe, idempotent startup migration point for future room-schema changes.

**Non-Goals:**

- Persistent inventories, character statistics, quests, or cross-restart state.
- Arbitrary scripting, arithmetic expressions, boolean operators beyond AND, or
  automatic migration of existing content.
- Direct administrator mutation of another live player's property values.

## Decisions

### Keep property state beside live session state

Introduce a small properties model owned by the gameplay/session layer. It uses
a session-specific key, then owner id, then variable name. This naturally gives
guests unique state without synthetic persistent ids and lets session removal
discard all values in one operation. The model never participates in
`PersistenceController.save()`.

Alternative considered: attach a property dictionary directly to `Session`.
Rejected because shared validation, condition evaluation, effects, and limits
would then be duplicated across controllers and harder to test independently.

### Model conditions and effects as data validators

Centralize validation for condition triples and effect pairs in the new model,
and call it from rooms/items load validation and all editing mutations. Persisted
metadata remains JSON lists: a condition field is a list of
`[name, operator, value]`; an effect is `[name, value]`. Empty condition lists
are the normalized no-gate state; the startup migration fills omitted condition
fields with empty lists.

Stored numeric values and numeric condition operands are integers from 0 through
100. Numeric effect operands are signed integer deltas; their resulting stored
value clamps to that range. Strings replace values. The per-owner six-property
limit is checked only when inserting a new name, so updates still work at the
limit.

Alternative considered: represent operators and values as objects. Rejected to
match the requested compact, editable JSON shape and minimize Pico memory.

### Normalize persisted room schema at startup

Add a migration coordinator invoked after `PersistenceController` loads records
and before its normal cross-model validation. Its first migration recursively
fills only missing condition-array fields with `[]`: `unlocked_if` on rooms,
`visible_if` on items, and `available_if` on interactions. It never rewrites a
present value, so validation remains the authority for malformed records.

The coordinator reports whether it changed room data and publishes that changed
room collection once, letting the existing dirty-save machinery persist it. Each
startup runs the migration list in version order; individual migrations must be
idempotent, permitting future schema additions without version metadata in every
record or a separate migration journal.

Alternative considered: use absent optional fields indefinitely. Rejected
because the project needs a predictable schema and a reusable path for future
normalization. Alternative considered: silently replace malformed present values.
Rejected because it loses builder data and hides corruption.

### Keep home rooms reachable

Room 1 and every user's configured personal home must remain public and ungated.
The room model rejects unlock-rule changes for a home room, room editing rejects
making a home private, and load validation rejects persisted homes that are
private or already have rules. Items and creatures inside home rooms remain
independent content and may use visibility conditions or variable effects.

### Make visibility and entry predicates session-aware

Add shared predicates for: a session satisfying conditions for an owner; a
session seeing an item; a session using an action; and a session entering a
room. The existing `Session.can_enter()` remains the common movement boundary
and gains the destination-room condition, with the destination owner used as
the property scope. Owner/admin bypass applies to conditions but not property
effects.

Room/item controllers filter before rendering, target resolution, lists, and
inspection. Item action lookup filters available actions before `/use` selects
the sole action or an action verb resolves it. This prevents hidden records from
leaking through alternate views.

Alternative considered: only check conditions at command dispatch. Rejected
because room rendering, target lookup, list output, cron effects, and movement
would drift or expose hidden data.

### Configure metadata through existing command families

Extend current owner/admin commands rather than introduce a separate command
namespace. Use `/room-unlock-rules` for room conditions, `/item set ... visible`
for item visibility, `/interaction require` and `/interaction set` for action
conditions and effects, and `/habit set` for cron effects. `/interaction clear`
and `/habit clear` remove their corresponding effects; every condition command
has an explicit `clear` form. Variable names use lowercase identifier syntax;
quoted values are always strings while unquoted integer tokens are numbers. The
implementation validates complete replacements before publishing and documents
the exact forms in `/help programming`.

Alternative considered: a new `/variable` command family. Rejected by the
product decision to keep content configuration alongside the object it affects.

### Organize focused help around player intent

Keep normal `/help` as the complete command index, but place a short focused-help
menu before it. The five topic names, `tutorial`, `user`, `movement`, `building`,
and `programming`, are handled by the command controller rather than registered
as ordinary commands. Each topic renders introductory prose first, then reuses
the existing command metadata and permission filtering to show its relevant
commands. This keeps syntax and permissions synchronized with the command
registry while avoiding five independent help tables.

`/help programming` owns the variable explanation, because variables are used
to program interaction and habit behavior. This replaces the narrower
`/help variables` topic.

Alternative considered: retain one long tutorial plus a separate variables page.
Rejected because it makes common workflows hard to find and gives variables an
unnecessarily isolated entry point.

### Deliver cron effects per live occupant

At a due cron job, the scheduler snapshots current live room occupants, applies
the configured effect independently to each, and sends their result through the
normal session notification path. Output emote/chat ordering stays unchanged;
property notifications are separate per-recipient messages. An effect that fails
for one recipient, such as a full owner scope, does not prevent output or effects
for other occupants.

Alternative considered: a shared room property value. Rejected because player
progress must remain individual.

## Risks / Trade-offs

- [More fields in nested room records increase malformed-data risk] -> Validate
  every optional field at load and reject invalid records before serving players.
- [Conditional checks may leak hidden content through an overlooked view] -> Route
  every room/item/action presentation and target-resolution path through shared
  visibility predicates and test each exposed command.
- [Frequent cron effects can fill a property's six-variable limit] -> Existing
  names continue to update; only new names fail, with an actor-specific message.
- [Multiword names complicate parsing] -> Reuse the existing quoted-argument
  parser only for string values. Identifier-style variable names eliminate
  multiword-name ambiguity; help examples distinguish quoted string values from
  unquoted integers.

## Migration Plan

1. Deploy code that treats every new metadata field as optional.
2. Existing `users.json`, `rooms.json`, and `mail.json` load, then the startup
   migration adds the required empty condition arrays to `rooms.json` and saves
   it once after validation.
3. Builders configure conditions/effects only after deployment. Live properties
   begin empty and clear safely on restart or disconnect.
4. Roll back by deploying the prior code only after removing the new optional
   room metadata from `rooms.json`, because older load validation will reject it.

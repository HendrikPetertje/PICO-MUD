# Design

## Context

See proposal.md for scope. The current device has a working poll-based telnet
transport, 2048-byte input cap, 4096-byte output cap, 100 ms controller tick,
6-client limit and MVC boot wiring. The bootstrap controller only handles quit.
The archived change measured 431200 free heap bytes after startup on Pico 2 W /
MicroPython 1.29.0. Real gameplay allocations and save pauses are unmeasured.

`modules/telnet.py` currently discards negotiation, yields decoded lines, closes
on raw output overflow and processes truncated prefixes. The application needs
real dispatch, exact password text, truncation notification and flow-controlled
responses. `config.py` already defines all world limits. No persistent models
or data files have been implemented. The reference controller mixes data and
rendering and keeps data only in RAM; it is not a persistence template.

## Goals / Non-Goals

**Goals:** Deliver the complete command contract with explicit model ownership,
one shared movement/permission path, reusable notifications and selective
persistence. Keep memory bounded and verify the whole player/build/save loop.

**Non-Goals:** Invent a generic ORM, channels, a scripting engine, portable
inventory, internet services, password masking or a permanent test suite.
Do not introduce device deployments during planning. No per-command disk writes.

## Decisions

### 1. Concrete MVC boundaries

```
target/
  main.py                         construct shared objects and boot
  config.py                       settings only
  modules/
    wifi.py, led.py                existing hardware utilities
    telnet.py                     transport plus capacity/truncation hooks
    command_parser.py             small quote-aware token/remaining-text parser
  models/
    storage.py                    shared JSON file/dirty-save helper
    users.py                      user records, hash verification, users save unit
    rooms.py                      rooms/exits/nested item storage, rooms save unit
    items.py                      room-local item/action operations via rooms
    mail.py                       inboxes and mail save unit
  controllers/
    telnet_controller.py          transport events, route to session/commands
    session_controller.py         pre-login/password/playing state and live roster
    command_controller.py         registry, permissions, lookup and help routing
    room_controller.py            shared movement and room/exit editing
    item_controller.py            item editing and static actions
    communication_controller.py   say/emote/whisper/page/shout
    notification_controller.py    session/user/room/global recipients
    mail_controller.py            own-inbox operations
    admin_controller.py           account lifecycle, coordinated cleanup, uptime
    persistence_controller.py     startup validation, initialization, periodic save
  views/
    telnet_view.py                login and generic replies
    room_view.py, item_view.py     exploration and editing output
    notification_view.py          presence/chat presentation
    mail_view.py, admin_view.py    inbox/account listings
    help_view.py                  registry-driven help
```

Use simple explicit constructor injection and one instance per model for the
application lifetime. Models do not import controllers or socket code. Views
take values and return strings/iterators; they do not mutate models. Controllers
coordinate actors, permissions and cross-model operations. Utilities remain
domain-neutral. Smaller combined view files are acceptable if responsibility
stays clear; do not create a generic MVC framework or one class per command.

### 2. Storage and numeric IDs

Users and rooms remain top-level JSON arrays, indexed in memory by integer id.
Use the same record objects for indexing and serialization, not a second copy
of the world. Items operates on Rooms' nested collections and marks Rooms dirty.
Mail keeps integer user keys in memory, streaming an object with decimal string
keys at the JSON boundary. No separate item file/save cycle.

Allocate user/room ids above the maximum live id and all surviving references
at load, then monotonically for the running application. Deletion cleans all
references before reuse could matter; there are no durable session IDs. An item
move allocates a destination-local id distinct from the moved source id and
existing destination ids; source and destination room identify different scopes.
Avoid a new metadata file solely for permanently non-reused ids, which the
outline does not require.

Storage validates types (exclude bool for integer fields), uniqueness, foreign
keys, owners, protected user/room 1, same-owner exits, home ownership, field
limits and interaction references before serving players. Deleting a user
removes their authored mail so no historical sender tombstone is required.

### 3. Initialization and save failure behavior

At boot, load all files and validate them together. If none exist, build user 1,
public room 1 and empty mail, then save before opening the telnet listener.
Missing mail with valid users/rooms can be initialized independently. Partial
users/rooms state or corrupt data stops boot and preserves files for admin
inspection; do not silently reset the world. Temporary files never take
precedence over valid primary files.

Storage.save_if_dirty streams JSON through `json.dump` into a same-directory
temporary file, closes it, then renames over the primary and clears its dirty
flag. Use compact separators. No `json.dumps` of the whole world and no read-back
comparison. On error retain dirty state and continue attempts on the other
models; report failures to serial and `/save` callers.

The persistence controller uses wrap-safe elapsed-time accumulation from the
existing tick; it invokes file owners every SAVE_INTERVAL (30 seconds). `/save`
uses the same path. Startup initialization is the explicit exception to waiting
for a timer. Shutdown is not assumed to flush uncommitted changes.

Temporary-file replacement protects an individual file under the device's
filesystem guarantees, not a transaction across all three files. A power loss
between file replacements can leave cross-file inconsistency; validation will
stop boot instead of repairing/destructively guessing. Keep this limitation
documented, preserve backups before deployment and before fault injection.
An atomic multi-file snapshot/journal would be a later change, not silently
promised by three independent renames.

### 4. Mutation and memory discipline

Before a multi-record operation, validate permissions, quotas, destination slots
and references and build any new records before publishing them. Models mark
dirty only after actual changes. User creation must not leave a home without
a user or vice versa. Item move must not delete the source before validation.
Deletion gathers affected ids, removes incoming references and relocates sessions
in one controller turn; no yields during a world mutation.

Use gc.collect()/gc.mem_free() before operations that grow state, including
description expansion and mail. Respect the existing 32768-byte reserve without
claiming that it guarantees all configured maxima fit. Keep temporary mutation
work small; catch expected validation errors as command errors. Unexpected
allocation failures must not be converted into success or leave an unmarked
partial mutation. Measure imports, representative data and save duration on
device. `.mpy` compilation is an optional measured mitigation, not a new hard
dependency or permission to reduce scope silently.

### 5. Sessions and login

SessionController maps connections to transient state: awaiting login,
awaiting password, or playing. Registered sessions reference a user id; guests
have generated unique guest-N names. A user-id index points only to the latest
live session. Successful replacement removes old gameplay presence before
closing its socket; old disconnect callbacks compare session identity and cannot
delete the replacement. Re-check current admin/banned flags on every command.

`/connect name` stores only the pending name and consumes the next line as exact
password text. `/connect name password` uses the parser's remaining password
argument, accepting visible input. No echo suppression is required, so the
existing no-negotiation-response transport contract stays intact. Do not log
submitted credentials. Clear pending credentials/state after success, failure
or disconnect. Guests have no user record or inbox.

Stored password is `binascii.hexlify(hashlib.sha256((salt + password).encode()).digest()).decode()`.
MicroPython lacks hexdigest; do not substitute an unavailable desktop method.
This is the agreed shared-salt representation, not a slow password KDF. Config
defaults seed new installations only; changing config later does not reset users.

### 6. Command registry and lookups

The command-contract document is the exhaustive coverage matrix. Registry
entries include canonical verb, aliases, permission, syntax/help and handler.
Reserve the union of verbs/aliases for item actions. Parsing is small and
quote-aware, without relying on unavailable shlex: return token spans so the
handler can retain the final text exactly. Preserve Unicode display strings;
use lowercased exact comparisons for names and aliases. Duplicate local item
names return ids to disambiguate.

Commands validate actual ownership on the target, not merely the player's
current room. Admins may edit another owner's room, but new rooms/items remain
owned by that property owner and all quotas apply to them. Model methods retain
ownership/id invariants regardless of caller. User 1 cannot be banned/demoted/
deleted. Room 1 cannot become private or be removed. No command exposes another
user's mail or credentials.

### 7. Shared movement, privacy and notification paths

RoomController.move validates destination and optional exit lock, then sends
old-room departure, changes location, sends arrival and returns the destination
view. ItemController delegates teleports here; it never assigns session location
directly. Cross-owner exits are prohibited for everyone; cross-owner public-room
teleports work. Explicit admin teleports may enter private rooms. An exit lock
blocks even admins, while explicit teleport is independent of exit traversal.

Room privacy changes evacuate unauthorized occupants to room 1. Deleting rooms
or users cleans exits and item teleport targets; clearing a target retains the
interaction's flavor/action. Home rooms are protected except during removal of
their owning user. Room 1 stays fixed when user 1 changes personal home.

Notifications scan live sessions (at most 6 by default), select recipients and
use views plus buffered transport. A notification failure cannot undo a successful
move or stop other recipients. Room speech includes the sender; arrivals/departures
exclude the actor. No notification channel index or durable message queue.

### 8. Bounded responses through a small output buffer

Large `/help`, `/rooms`, `/items`, `/users` or full room views can exceed 4096
bytes, especially with UTF-8. Do not increase the buffer or concatenate whole
outputs to hide the issue. Add a transport capacity query and non-destructive
try-send operation that returns false if a chunk does not fit. Preserve raw
send's overflow protection. Keep capacity checks in bytes after CRLF expansion.

Each session owns at most one response iterator and one pending chunk. Views
yield lines or bounded text pieces; split long pieces on UTF-8 boundaries.
Controller ticks enqueue a limited amount per session as capacity permits.
Prompt is the last chunk. No unbounded pending-command list: while a response
is active reject additional commands with a coalesced busy notice; `/quit` may
cancel output and close. Notifications use bounded best-effort enqueue and can
coalesce a missed-notifications notice for slow readers. Release iterators on
disconnect/replacement.

Do not iterate a mutable dictionary while another session may edit it on a
later tick. Use bounded id snapshots for large lists and re-resolve/permission
check each entry; disappeared entries are skipped. Inbox lists are only ten
entries; copy the selected message's display values when reading. Render final
prompt once and do not duplicate it around an active response. Pre-login and
password-prompt sessions do not receive gameplay notices.

### 9. Overlong input and expected failures

Current transport silently passes a truncated prefix. Add a controller event
for a line exceeding MAX_LINE_LENGTH instead; reset at its delimiter and reject
the entire command/password. Preserve exact text delivery otherwise. Update the
existing telnet spec rather than contradict its truncation behavior silently.

Expected bad arguments, denied permissions, unavailable targets and quotas
return domain errors rendered by the controller with a fresh prompt. Unexpected
client-handler errors retain the existing isolation behavior. Save failures are
caught by the persistence controller so they cannot escape on_tick and kill the
server. Fatal boot/data-integrity failures still use the existing LED/serial path.

## Risks / Trade-offs

- **RAM grows with world data:** configured ceilings exceed guaranteed capacity;
  admission checks and device measurements remain essential. Do not lower agreed
  limits without the user's decision.
- **Synchronous flash saves briefly pause polling:** stream saves every 30 seconds,
  measure pause duration with representative data; do not add threads preemptively.
- **Cross-file power loss:** per-file replacement is not transactional; preserve
  files and stop on inconsistent boot data. Recovery needs an admin backup.
- **Slow clients:** bounded response state and transport limits preserve other
  clients; notifications may be coalesced rather than retained indefinitely.
- **Public defaults and visible passwords:** intentional local-project behavior;
  keep clear config guidance and exclude credentials from output/logs.

## Migration Plan

No legacy game database exists in the bootstrap. Before implementation upload,
inspect the device filesystem and back up any `/data` that appeared since this
plan. Deploy packages, including new models, but never overwrite existing data
or an admin's customized config blindly. First run seeds only a new world.
For rollback, restore prior code/config; preserve the database separately rather
than deleting it. Document the exact deployed firmware and commands.

Verification uses local/USB exercises and the user-operated multi-client
walkthrough in `documentation/acceptance.md`. Keep observed checks distinct from
user confirmations and leave task checkboxes open until their verification is
satisfied. Planning ends at artifact review; `/opsx-apply complete-mud-gameplay`
starts implementation in a subsequent request.

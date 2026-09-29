# Tasks

## 1. Transient Properties And Persisted Metadata

- [x] 1.1 Add the session-properties model with owner-scoped six-variable limits, condition evaluation, signed numeric effects, string replacement, and property formatting; verify focused unit tests cover guests, owner isolation, all-condition matching, type mismatches, clamping, and limit failures.
- [x] 1.2 Extend room/item record validation and safe replacement operations for `unlocked_if`, `visible_if`, `available_if`, and `set_variable`; verify valid nested metadata round-trips and invalid names, operators, values, and shapes fail without modifying records.
- [x] 1.3 Add the idempotent startup migration coordinator and its initial room-schema migration for missing condition arrays; verify an older `rooms.json` is upgraded and saved once, a second boot does not rewrite it, and malformed present fields still halt startup without replacement.
- [x] 1.4 Update `openspec/PROJECT_OUTLINE.md` in the same patch as migration and validation changes with normalized condition arrays, optional property effects, and builder command forms; verify every documented field, semantic, and command name matches the implemented contract.

## 2. Session And Access Integration

- [x] 2.1 Wire the properties model through application, telnet, and session lifecycle dependencies, clearing state on disconnect, replacement, ban, timeout, and restart; verify reconnecting users and guests start without prior values.
- [x] 2.2 Extend shared room-entry checks to enforce `unlocked_if` for walking, teleporting, joining, and item portals while preserving owners/admin bypasses and visible source exits; verify failed entry leaves location and notifications unchanged.
- [x] 2.3 Filter room presentation, item/creature lookup, examine, owned-item lists, interaction lists, `/use`, and action dispatch through shared item/action visibility checks; verify unmet conditions neither resolve nor leak while owner/admin views remain available.
- [x] 2.4 Apply interaction effects before optional movement and apply due cron effects independently to all live room occupants without changing emote/chat output order; verify per-recipient updates, a full scope affecting only that recipient, and no effects from empty rooms.

## 3. Builder And Player Interface

- [x] 3.1 Register and implement `/room-unlock-rules add|remove|clear` with identifier-style variable names and atomic validation; verify owners and admins can manage a room's conditions, room 1 remains public, and invalid edits preserve the room.
- [x] 3.2 Implement `/item set <item> visible add|remove|clear` for item/creature visibility metadata; verify owner/admin edits, persistence, and visitor visibility behavior.
- [x] 3.3 Extend `/interaction require` with add/remove/clear forms and implement `/interaction set` plus `/interaction clear` for action effects; verify configured actions remain bounded, atomic, hidden when unavailable, and apply effects when used.
- [x] 3.4 Implement `/habit set` and `/habit clear` for cron effects; verify configuration, persisted validation, per-occupant delivery, and unchanged existing cron output behavior.
- [x] 3.5 Add property values to `/look at self` and `/look at <player>` and result notifications, then implement public `/help programming`; verify guests can read help and inspect live values, while no command directly sets another player's properties.
- [x] 3.6 Add focused `/help tutorial`, `/help user`, `/help movement`, `/help building`, and `/help programming` topics with introductions and permission-filtered command lists; verify normal help advertises all topics and guest/owner views expose only permitted commands.

## 4. End-To-End Verification

- [x] 4.1 Add integration tests covering a hidden key/treasure flow, a room unlock, a conditionally available creature action, numeric buff/debuff habits, owner/admin bypasses, guest state, and reset on disconnect; verify the full test suite passes.
- [x] 4.2 Run OpenSpec validation with `openspec validate add-session-properties --strict` and run the repository test command; verify the proposal artifacts, schemas, migrations, and implementation checks all pass.

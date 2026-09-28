# Tasks

One coordinated implementation, ordered by dependency. No permanent unit or
integration suite is required. Use temporary local/USB exercises and the manual
walkthrough; record actual observations separately from user confirmations.
Do not mark a task done when its stated verification is still pending.

## 1. Model foundation and persistence

- [x] 1.6 Set MAX_DESCRIPTION_LENGTH=600 for room/item/exit description edits and loaded data, preserving MAX_TEXT_LENGTH=250 for activation/flavor/chat/mail text; verify Unicode 600/601 boundaries, save/reload and unchanged message limits, and update documentation.

- [x] 1.1 Add the models package and shared storage helper for streamed load/dump, dirty ownership and same-directory temporary replacement. Verify on disposable data that clean saves do not write, failed saves retain dirty state and a later retry succeeds; document verified firmware/file API behavior in `documentation/micropython-data.md`.
- [x] 1.2 Implement users and rooms models with numeric IDs, record validation, ownership, home references and configured limits. Verify invalid types, duplicate IDs, dangling references and cross-owner exits are rejected without overwriting input files, and valid data round-trips through JSON.
- [x] 1.3 Implement the items model over shared room storage and the mail model with integer in-memory keys/canonical JSON string keys. Verify an item mutation dirties only rooms, mail mutation dirties only mail, reads stay clean and no duplicate item database is created.
- [x] 1.4 Implement the persistence controller's boot load/validation, first-world seed (user 1/room 1), missing-mail initialization and selective 30-second save scheduling. Verify a fresh world, unchanged reboot, partial/corrupt-file refusal and per-file retry in a disposable setup; document the cross-file power-loss limitation and recovery steps.
- [x] 1.5 Validate the existing config's gameplay limits and apply memory admission to state-growing operations. Verify quota boundaries, no-op edits, rejected mutations and low-memory behavior; record baseline heap after imports/seed and confirm all configured limits remain as agreed.

## 2. Transport and command foundation

- [x] 2.1 Extend telnet with capacity-aware non-destructive enqueue and whole-line overflow reporting while preserving raw-send overflow protection and existing framing. Verify partial writes, UTF-8 chunk boundaries, rejected truncated command/password prefixes and recovery on the next line on the Pico or a clearly identified local adapter.
- [x] 2.2 Add the quote-aware parser and central command registry with every command/alias from `documentation/command-contract.md`. Verify quoted multiword targets, escaped quote/backslash, final-text preservation, mail delimiter parsing and reserved action names; update the contract examples to match the parser exactly.
- [x] 2.3 Add bounded per-session response iteration, one pending chunk, final prompts, busy handling and release on disconnect. Verify a response larger than 4096 bytes completes without overflow, a second client remains responsive, mutations between listing chunks do not leak inaccessible data, and incoming commands cannot create an unbounded backlog.

## 3. Accounts and live sessions

- [x] 3.1 Implement shared-salt SHA-256 verification, own-password change and admin password-setting model operations. Verify hash representation with `binascii.hexlify`, old/new password behavior, Unicode/whitespace passwords and persistence; inspect that credentials are absent from logs and user-facing records.
- [x] 3.2 Implement pre-login, password-prompt and playing states, inline/prompted connect/login, guest identities and room-1 entry. Verify allowed pre-login commands, visible password compatibility, guest restrictions, invalid/banned login and welcome/navigation output; document login examples.
- [x] 3.3 Implement the user-to-live-session index, successful replacement and exactly-once disconnect cleanup. Verify wrong-password replacement leaves the original online, successful replacement kicks it, stale callbacks cannot remove the new session and session movement never dirties models.

## 4. Notifications and communication

- [x] 4.1 Implement notification controller/view delivery to session/user/room/all using the live roster. Verify guest recipients, actor exclusions, offline handling, isolated failed recipients, bounded slow-client notices and prompt behavior without a subscription registry or durable backlog.
- [x] 4.2 Implement say/emote shortcuts, whisper, page and admin shout through the notification path. Verify room isolation, sender confirmation, guest messages, private recipient checks, text limits and zero database writes; record a two-room communication walkthrough.

## 5. Rooms, exits and exploration

- [x] 5.1 Implement the shared movement path for directions, all home/global-home aliases, room-id teleport and join. Verify locks block everyone, admins may enter private rooms, guests have no personal home, successful movement notifications are ordered and failed/same-room moves do not announce.
- [x] 5.2 Implement room creation/linking and exit edits with actual owner quotas and same-owner restrictions. Verify all dig/undig/rename/describe/message/lock/unlock commands, occupied reverse-slot failure, cross-owner rejection even for admins and no partial updates; document representative build commands.
- [x] 5.3 Implement private toggles, visitor evacuation, personal sethome and room deletion/reference cleanup. Verify room 1 stays public/undeletable after the admin changes personal home, current personal homes remain protected and deleted targets leave no incoming exits or item teleport references.
- [x] 5.4 Implement look/l, look-at, examine/ex, exits, rooms, items, who and whoami with views and visibility rules. Verify local item IDs/name ambiguity, player identity display, hidden private locations/contents and large Unicode listings; ensure documented help reflects actual permissions.

## 6. Items and interactions

- [x] 6.1 Implement create/rename/describe/destroy/move for room-local items. Verify owner/admin permissions, same-owner destination, destination-local new identity, preserved content, full-room failure without source loss and absence of inventory commands.
- [x] 6.2 Implement action add/update/remove/teleport/list plus dynamic action execution and use. Verify two-action limit, all reserved aliases, flavor updates, target clearing, guest interaction, cross-owner public-room teleport and current privacy checks; confirm execution never dirties the item and update help/examples.

## 7. Mail and administration

- [x] 7.1 Implement mail send/list/read/delete and bounded mail views. Verify private access even for admins, self/offline delivery, online notices, ten-mail boundary, title/body lengths, numeric renumbering and saved Unicode round-trip; document the exact mail syntax.
- [x] 7.2 Implement user create/remove/ban/unban/admin/password and users listing. Verify user/home creation has no partial records, permissions update immediately, bans disconnect, user 1 protections hold, deletion cleans property/inboxes/authored mail/references and credentials never appear; record administration examples.
- [x] 7.3 Implement boot, save and uptime plus registry-generated help for all commands. Verify clean/dirty/failed-save replies, live user/guest boot behavior, elapsed time and memory/count output; audit every row and alias in the command contract against registered handlers.

## 8. Wiring, deployment and full acceptance

- [x] 8.0 Add the user-supplied seven-line PICO MUD block-art banner to the pre-login view, preserving UTF-8, spacing and line breaks; verify complete streamed delivery before login instructions and prompt without overflowing the transport buffer.

- [x] 8.1 Wire shared models/controllers/views into main and telnet callbacks, replace the construction welcome and retain Wi-Fi/LED behavior. Verify startup initializes/loads data before accepting gameplay, ticks drive saves/output with no clients, and expected command errors preserve the session; update deployment docs for new packages while preserving device config/data.
- [x] 8.2 Run the complete disposable-world walkthrough in `documentation/acceptance.md`, including restart, permissions, memory/quotas, failed saves, long output and referential cleanup. Record each result and firmware, imported/seeded/populated heap and save durations; resolve failures before marking complete.
- [x] 8.3 Back up current device data/config, deploy the reviewed change over USB with user authorization and perform the user-operated multi-client acceptance. Record user confirmation separately from local/USB checks, preserve backups, leave normal startup running and validate OpenSpec artifacts before requesting archive.

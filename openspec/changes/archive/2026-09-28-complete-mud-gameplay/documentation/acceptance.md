# Manual acceptance walkthrough

Run only during implementation/verification, not while planning. Back up device
data before any destructive/corrupt-file exercise; use a disposable data directory
for fault checks. No permanent automated test suite is required.

## 1. Fresh startup, reload and identity

- Start with an explicitly empty test data directory. Confirm user 1, public
  room 1, empty mail, numeric references and config password hash representation.
- Restart and confirm no reset or unnecessary rewrite of valid records.
- Connect guest, admin and two ordinary accounts (Adam/Bob). Try inline and
  prompted login, wrong password, Unicode password and whitespace preservation.
- Reconnect as Adam: only the replacement session remains active. A wrong
  replacement password must not kick the real Adam.
- Confirm pre-login clients have no presence, room details or gameplay messages.

## 2. Full command coverage

Use every row and alias in `command-contract.md`, not only the happy-path
examples below. Record skipped checks and their reason instead of marking the
whole group done. Verify help matches the implemented registry.

## 3. Properties and permissions

- Adam digs rooms up to quota, names/describes them, edits exit names/text,
  locks/unlocks and removes an exit. Check opposite exits and occupied-slot errors.
- Try linking Adam's room to Bob's public room as both Adam and admin: reject.
- Bob tries building in Adam's room: reject. Admin edits it: allow, retaining
  Adam's ownership and charging Adam's quota.
- Set Adam's room private: visitors move to room 1, Bob/guest entry fails,
  admin entry succeeds. Check who/items/rooms do not leak inaccessible details.
- Move user 1's personal home elsewhere: all global-home variants still use room 1.
  Refuse deleting/private room 1 and deleting any current personal home.

## 4. Items, interaction and cleanup

- Create two-action item; inspect, rename and describe it. Reject a third action
  and reserved names such as `look`, `mail`, `n` and `use`.
- Update existing action flavor, set/clear target and remove an action.
- Guest uses an item teleport to Bob's public room: allow. Make target private:
  deny ordinary entry but allow admin. No interaction dirties the world.
- Move an item between Adam's rooms: preserve content, recreate local identity.
  Full target or differently owned target fails without losing source item.
- Delete a non-home target room: incoming exits and item teleport targets are
  cleaned and occupants relocated. Delete a user: property, inbox and authored
  mail are removed; user 1 is protected.

## 5. Communication and mail

- Observe departure/arrival order and exactly-once logout/replacement notices.
- Say/emote reaches only the current room including sender; whisper is same-room
  private; page reaches another room and guests; shout is admin-only.
- Send Unicode mail to online/offline recipients; only online ones get notices.
  Fill ten slots and reject the eleventh. Read/delete/renumber, reject invalid
  numbers, verify admins cannot read another inbox.
- Save and reboot; mail, rooms/items, passwords and flags survive while session
  locations/presence do not.

## 6. Moderation and resources

- Ban an online user, reject relogin, unban, reset password, toggle admin rights
  and verify the next command sees changed rights. Boot guest without banning.
- Exercise MAX_USERS, per-owner rooms, per-room items, per-item actions, text
  lengths and low-memory admission, restoring temporary settings afterwards.
- Send overlong lines containing a valid command prefix; no prefix may execute.
- Request help/room/user listings longer than 4096 bytes with Unicode fields.
  Verify complete incremental output and final prompt; another client stays fast.
- Stop reading on one client: output/response state stays bounded, other clients
  remain responsive, and there is no notification backlog or stale session.

## 7. Saves, faults and measured device check

- Record write counts or file checks: only dirty files change after 30 seconds;
  `/save` flushes immediately, reads/walking/chat do not write, no-op edits stay clean.
- Inject save failure in a disposable setup: dirty state remains, other file
  saves are attempted, retry succeeds, server stays responsive.
- Corrupt a disposable JSON or create a partial users/rooms pair: boot stops,
  reports diagnostic and preserves input files. Restore backup afterwards.
- Record firmware, imported-code heap, seeded-world heap, representative-world
  heap, maximum listing queue use and save duration. Compare against bootstrap
  free heap 431200 bytes without claiming configured maxima are guaranteed.
- Upload reviewed code over USB preserving real data/config; user verifies
  Wi-Fi/telnet while the assistant retains internet access. Leave the normal
  application running after serial diagnostics and record final acceptance.

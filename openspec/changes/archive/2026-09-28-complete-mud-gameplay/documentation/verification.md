# Implementation verification — 2026-09-28

## Delivered and deployed

The complete command registry, models, feature controllers, views, streamed
responses and user-supplied pre-login banner are implemented. No persistent
test suite or external runtime package was added. The live Pico was started
normally after verification; the test users/worlds were disposable, not seeded
into the live `/data`.

Device: Pico 2 W / RP2350, MicroPython 1.29.0 dated 2026-08-24,
USB `/dev/cu.usbmodem2101`. Initial filesystem contained bootstrap files only.
Backup of original config/main/modules/controllers/views:
`/var/folders/0_/0_kt31817cxf98vnlpfhrczc0000gn/T/opencode/pico-bootstrap-backup/`.
No existing data directory needed backup. Config was compared: only the welcome
text and a save-interval comment changed, with credentials/settings preserved.

## Checks passed

Temporary scripts outside the repo were run locally and, where noted, directly
on the Pico through USB. Script cleanup removed only its disposable directories.

- **Storage/model checks (local and Pico):** compact streamed JSON, numeric ids,
  canonical mail keys, clean saves, failed-write dirty retention, retry, other-file
  saves after failure, malformed/partial data preservation, duplicate ids, bool
  references, unknown owners and cross-owner exit rejection.
- **Whole command walkthrough (local and Pico):** admin/guest/prompted/inline
  login, Adam/Bob creation, wrong-password replacement, stale-session cleanup,
  password changes, guest restrictions, inspection, room/exit editing and locks,
  all home forms, fixed global room 1, occupied exit rejection, privacy evacuation,
  admin edits, static portals, item move/action updates, mail, chat, moderation,
  user/room cleanup and saved-world reload.
- **Resource checks (local and Pico):** configured user/room/item/action/mail
  caps, reserved action names, text limits, simulated low heap, whole-line
  truncation rejection, 7500-character Unicode streamed response, bounded
  non-reading-client state and coalesced busy handling.
- **Presentation/notification checks (local and Pico):** pending room-tagged
  chunks recheck accessibility after privacy edits; full/closed recipients do
  not block other recipients; no unbounded notification or command backlog.
- **Real host TCP sockets:** actual transport with MicroPython clock/poll
  adapters handled multi-client login, help, chat, portal movement, capacity
  rejection, overlong input and quit. This complements USB checks; it is not
  a claim that external Pico Wi-Fi acceptance was performed by the agent.
- **Review:** MVC ownership, limits, password/log exposure, no arbitrary code
  execution, same-owner exits, admin/mail boundaries, duplicate-login cleanup,
  save-failure isolation and streamed-output lifecycle were inspected.

The real-socket check caught a prompt/response completion race: the client could
submit its next command after seeing the prompt but before the iterator was
released. A terminal response chunk now releases the response before its prompt
is flushed. Subsequent local and Pico walkthroughs passed.

The printed ENOENT traceback in fault checks is intentional: the disposable
save path was made unavailable to verify dirty-state retention and retries.

## Measurements

Final normal startup after garbage collection: **375040 free heap bytes**.
With the larger edge-check harness loaded: **364832 bytes** after seed,
**331072 bytes** with its populated world; representative three-file save:
**87 ms**. These are observed workloads, not a promise that every configured
maximum fits. The temporary full-command harness finished with 362752 bytes.
Output queue remains capped at 4096 bytes.

Captured live startup: WPA2 AES hotspot at 192.168.4.1 and telnet port 8888.
Original network/LED implementation was retained.

## User acceptance

### Description-limit update

The earlier 400-character description check is superseded by the completed
600-character description update. Room, item and exit descriptions now share
MAX_DESCRIPTION_LENGTH=600; activation text, interaction flavor, chat and mail
bodies remain at MAX_TEXT_LENGTH=250. Local and Pico USB checks accepted 600
Unicode characters, rejected 601 without changing saved data, and reloaded the
description intact. Config validation includes the new setting. The update was
uploaded after a 31-second autosave wait and normal startup was restored.

The user confirmed on 2026-09-28 that the live MUD works for the features tried
so far and authorized marking the change complete, syncing specs and archiving.
This user-operated acceptance closes task 8.3. The normal Pico application was
left running after the deployment and description-limit update.

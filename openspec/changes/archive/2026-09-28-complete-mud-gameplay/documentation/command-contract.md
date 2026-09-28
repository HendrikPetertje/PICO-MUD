# Command contract

This table is the command coverage checklist for `complete-mud-gameplay`.
G means an active guest or registered player, U a registered player, O the
room/item owner or admin, and A admin. Before login allow only help,
connect/login and quit. Admin privileges never expose another user's mail.

## Parsing and naming

- Command words and aliases use lowercase matching; preserve display text and
  password case. Direction tokens accept north/east/south/west/up/down and
  n/e/s/w/u/d. Do not add diagonal directions.
- Double quotes group target names containing spaces. Within quoted arguments,
  `\"` and `\\` mean literal quote and backslash. Invalid quoting is an error.
  Final text is the remaining input, not rejoined whitespace-normalized tokens.
- A leading `"` on a gameplay line is the speech shortcut, not a target quote.
  Quotes inside slash commands follow the target grammar.
- Names use case-insensitive exact matching; reject ambiguity, do not use fuzzy
  prefixes. Usernames are unique single tokens, at most 60 characters, cannot
  be numeric-only or contain slash, quote, backslash or `=`; reserve `guest`
  and `guest-N`. Room/item names can contain spaces. Action names are single
  words and cannot collide with the dispatch registry's keys/aliases.
- Numeric item target `3` means item 3 in the current room. For shared editing
  commands, `here` and directions take precedence over item names; use item id
  to disambiguate. Player names resolve only to live sessions where required.
- Numeric references are positive base-10 integers. IDs are not booleans.
- Short names and mail titles use MAX_NAME_LENGTH (60). Room, item and exit
  descriptions use MAX_DESCRIPTION_LENGTH (600). Activation text, flavor text,
  mail bodies and chat use MAX_TEXT_LENGTH (250). Passwords are
  nonempty and at most MAX_TEXT_LENGTH; prompts preserve whitespace.
- Mutating text commands reject empty text. `none` clears only an interaction's
  teleport target; it is not a general null spelling.

## Session and inspection

| Syntax | Access | Behavior |
|---|---|---|
| `/connect <name> [password]`, `/login ...` | Pre-login | Inline login, or prompt for the password if omitted |
| `/connect guest`, `/login guest` | Pre-login | Enter as generated guest |
| `/quit` | Any command prompt | Goodbye and disconnect |
| `/password <old> <new>` | U | Verify old and replace own password hash; quote tokens containing spaces |
| `/help [command]` | Any | Available commands or detailed syntax; accept optional leading slash in help topic |
| `/who` | G | Live player names; hide inaccessible private location details |
| `/whoami` | G | Identity, id/admin/home for user, guest label for guest |
| `/look`, `/l` | G | Name, description, exits, items and players in current room |
| `/look at <target>` | G | Local item, exit or player; player shows identity/presence only |
| `/examine <item-or-dir>`, `/ex ...` | G | IDs/ownership/lock information; owner/admin sees interaction editing details |
| `/exits` | G | Current exits and lock state |
| `/rooms [user]` | U | Own or named owner's rooms, excluding inaccessible private rooms |
| `/items [user]` | U | Items in the requested owner's visible rooms, with room and local item ids |
| `/uptime` | G | Monotonic uptime, free heap, connection/user/room counts and limits |

## Movement and building

| Syntax | Access | Behavior |
|---|---|---|
| `/go <dir>`, `/<dir>` | G | Traverse unlocked exit to accessible room; show activation text |
| `/teleport home`, `/teleport to home`, `/home` | U | Personal home |
| `/teleport global home`, `/teleport to global home` | G | Fixed room 1 |
| `/teleport to <room_id>` | G | Any accessible room |
| `/join <player>` | G | Live player's accessible room |
| `/dig <dir> <room name>` | O | New room for source owner and opposite return exit; both slots required |
| `/dig <dir> to <room_id>` | O | Link same-owner existing rooms with opposite return exit; reject cross-owner link |
| `/undig <dir>` | O | Remove source exit only |
| `/rename here <name>` | O | Room name |
| `/describe here <text>` | O | Room description |
| `/private [on|off]` | O | Set or toggle; room 1 cannot become private; evacuate unauthorized visitors |
| `/sethome` | U, actual owner | Change personal home to current owned room; no admin ownership override |
| `/destroy room <room_id>` | O on target | Delete permitted non-home room; never room 1 |
| `/rename <dir> <name>` | O | Exit display name |
| `/describe <dir> <text>` | O | Exit look text |
| `/message <dir> <text>` | O | Exit traversal text |
| `/lock <dir>`, `/unlock <dir>` | O | Update source exit lock; locks block admins too |

`/dig north to 5` is the linking form. To create a room literally named
`to 5`, use `/dig north "to 5"`. Target-room and source-room ownership must
match even when an admin is acting. For a new room, charge quota to the source
owner rather than the acting admin. Room 1 can be renamed/described and have
items/exits; its identity, public status and existence are protected.

## Items

| Syntax | Access | Behavior |
|---|---|---|
| `/create <item name>` | O | Add local item owned through room |
| `/rename <item> <name>` | O | Rename local item |
| `/describe <item> <text>` | O | Edit local description |
| `/interaction add <item> <action> <flavor text>` | O | Add action or update existing action's flavor text |
| `/interaction teleport <item> <action> <room_id-or-none>` | O | Set accessible target or clear it |
| `/interaction remove <item> <action>` | O | Remove action |
| `/interactions <item>` | G | Action names; owner/admin also sees flavor and targets |
| `/<action> <item>` | G | Static flavor and optional actor teleport |
| `/use <item>` | G | Execute sole action, otherwise list choices/no actions |
| `/move <item> to <room_id>` | O on both | Same-owner rooms only; copy item content under destination-local id and remove source |
| `/destroy <item>` | O | Delete local item |

There is no take/drop/inventory. Duplicate room-local item names are permitted
but require numeric addressing when ambiguous. Reserve every built-in command
and alias as an action name; actions never shadow help/login/directions.

## Communication, mail and administration

| Syntax | Access | Behavior |
|---|---|---|
| `/say <text>`, `"text`, plain text | G | Room speech including sender |
| `/emote <text>`, `:text` | G | Room action including sender |
| `/whisper <player> <text>` | G | Same-room private message, sender confirmation |
| `/page <player> <text>` | G | Any live player/guest, sender confirmation |
| `/shout <text>` | A | All gameplay sessions |
| `/mail` | U | Own inbox numbered from 1 |
| `/mail read <number>` | U | Own message only |
| `/mail send <user> <title> = <message>` | U | Send to registered user, including self/offline; reject full inbox |
| `/mail delete <number>` | U | Delete own message, renumber remaining entries |
| `/user create <name> <password> [admin]` | A | User and owned home; optional literal `admin` enables admin rights |
| `/user remove <name>` | A | Delete user/property/inbox, authored mail and references; protect user 1 |
| `/user ban <name>`, `/user unban <name>` | A | Ban disconnects immediately; protect user 1 from bans |
| `/user admin <name> [on|off]` | A | Set/toggle admin rights; user 1 always admin |
| `/user password <name> <new>` | A | Reset hash; no old-password requirement |
| `/users` | A | Accounts and flags, no hashes/passwords |
| `/boot <player>` | A | Disconnect session without banning |
| `/save` | A | Save dirty file owners immediately, report results |

Mail splits at the first unquoted standalone `=` after recipient; title/body
must be nonempty. Subsequent equals signs remain in the message. A quoted title
can contain a literal equals sign. Inbox numbers are presentation positions,
not persistent IDs. Deleting a user removes their authored mail from other
inboxes to avoid dangling sender references.

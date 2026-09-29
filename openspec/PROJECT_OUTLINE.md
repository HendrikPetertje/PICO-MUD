# PICO MUD
PICO MUD is a lightweight, text-based multiplayer online game (MUD) designed
for the Raspberry Pi Pico W 2.
The code in /target of this repo is the code that can be uploaded to a Raspberry
Pi Pico W2 and will then have the following useful elements:

- On boot the Pico will create a wifi hotspot named "PICO MUD" (configurable).
  This hotspot is protected with a WPA2 password (configurable), so the admin
  invites players by handing out the wifi password. The Pico
  itself will always have 192.168.4.1 as its IP.
- An event loop on the Pico will expose a small telnet server on port 8888
  (configurable). Client machines can connect to this telnet server using
  `telnet 192.168.4.1 8888` and will be presented with a simple text-based
  interface to interact with the MUD.
- The connecting user can look around as a `guest` or login as a `user` with
  `password`. If a user is an admin, they can create or remove other users.

## Architecture (MVC)
The application follows Model–View–Controller (MVC). Paths below are relative
to `target/` in this repo; that directory's contents become the device root.

```
target/
  main.py                         boot and dependency wiring
  config.py                       configuration values only
  modules/
    wifi.py                       access point utility
    led.py                        LED utility
    telnet.py                     sockets, polling, framing and buffers
  controllers/
    telnet_controller.py          connection events and command dispatch
    session_controller.py         live sessions and player locations (later)
    notification_controller.py    direct, room and global delivery (later)
  views/
    telnet_view.py                plain-text responses and prompts
    notification_view.py          notification text and presentation (later)
  models/
    users.py                      user records and users.json dirty state
    rooms.py                      rooms, exits and rooms.json dirty state
    items.py                      operations on items nested in rooms
    mail.py                       inboxes and mail.json dirty state
  data/
```

This is the target architecture. The first boot/telnet change introduces the
utility modules, controller and view; models and additional feature
controllers/views arrive with their respective features.

- **Modules** handle reusable hardware and transport operations. Telnet
  reports connection events and decoded lines to controllers; it does not
  interpret game commands or access the database.
- **Controllers** handle every application interaction with telnet: commands,
  connection lifecycle, replies and notifications. They call models for data
  operations and views for text, then send that text through the telnet module.
  Controllers do not edit database records or dirty flags directly.
- **Views** format plain Unicode text. They have no socket access, model
  mutations or persistence logic; the telnet module handles UTF-8 and CRLF.
- **Models** own the authoritative in-memory database and its dirty state.
  There is one model for users, one for rooms and one for items in rooms.
  Mail has a separate model for its existing file. Model operations enforce
  data invariants; controllers handle command routing and player permissions.
- **main.py** wires dependencies, starts the utilities and controller, and
  handles fatal boot/runtime errors. **config.py** stays at the device root.

The items model uses the rooms model's nested item data without copying it.
Every successful item change marks the rooms model dirty; only the rooms
model saves `rooms.json`, including its items. There is no `items.json` or
independent item save cycle. Item operations use `(room_id, item_id)` because
item ids are local to a room.

## Users
Every user receives a base room (their home room), this is the room the user
teleports to when they `/teleport home`. Users can `/dig [cardinal|up|down]`
from their own rooms. Exits can only link rooms with the same owner; users
cannot link to another user's rooms, including public ones. Item interactions
can instead teleport players to another user's public room. Admins may edit
any owner's rooms, but must preserve the same-owner exit rule.

A user can own at most `MAX_ROOMS_PER_USER` rooms (default 10), including their
home room.

Users own the items in their own rooms. Users can only create and place items
in rooms they own, never in someone else's room. Items can not be picked up,
taken or carried by anyone. The `/look at` command allows looking at items.
Users (even guests) can interact with items; this is programmable in the MUD.
Interactions could be pushing, pulling, reading, pressing, etc. The
interaction is up to the fantasy of the user creating the item.
Interactions with an item never change the item, they merely present the user
with a flavor text as well as the ability to teleport the user to another room.
(The flavor text for this teleportation action can be changed: fall through a
hole, etc.)

Limits (all configurable in config.py):
- `MAX_ITEMS_PER_ROOM` (default 5)
- `MAX_INTERACTIONS_PER_ITEM` (default 2)

### Guests
Guests can walk around all rooms that are not private and can interact with
items. Guests can not build, edit, send or receive mail, or change anything in
the MUD. Guests get a generated name (`guest-1`, `guest-2`, ...) that only
lives for the duration of their session.

## Configuration
All configuration lives in `/config.py` (`/target/config.py` in this repo):

| Variable | Default | Description |
|---|---|---|
| `AP_SSID` | `"PICO MUD"` | Wifi hotspot name |
| `AP_PASSWORD` | `"MultiUserDungeon"` | WPA2 password of the hotspot. Must be 8-63 characters; the Pico refuses to boot the hotspot (fatal error) if it is not. |
| `TELNET_PORT` | `8888` | Port of the telnet server |
| `MAX_CLIENTS` | `6` | Maximum simultaneous telnet connections |
| `IDLE_TIMEOUT` | `900` | Seconds of inactivity before a session is disconnected |
| `ADMIN_NAME` | `"admin"` | Username of the initial admin (user_id 1) |
| `ADMIN_PASSWORD` | `"changeme"` | Password of the initial admin |
| `PASSWORD_SALT` | `"..."` | Shared salt used for hashing all passwords |
| `WELCOME_TEXT` | `"..."` | Text shown after logging in (user or guest) |
| `SAVE_INTERVAL` | `60` | Seconds between checks whether the state must be saved |
| `MAX_USERS` | `15` | Maximum number of users, including the admin |
| `MAX_ROOMS_PER_USER` | `10` | Maximum rooms a user owns, including the home room |
| `MAX_ITEMS_PER_ROOM` | `5` | Maximum items in a single room |
| `MAX_INTERACTIONS_PER_ITEM` | `2` | Maximum interactions on a single item |
| `MAX_NAME_LENGTH` | `60` | Maximum length of short labels: user, room, exit, item and action names, and mail titles |
| `MAX_DESCRIPTION_LENGTH` | `600` | Maximum characters in room, item and exit descriptions |
| `MAX_TEXT_LENGTH` | `250` | Maximum characters in activation texts, interaction flavor texts, chat and mail messages |
| `MIN_FREE_MEMORY` | `32768` | Bytes of free heap below which commands that create data are refused |
| `MAX_MAILS` | `10` | Maximum mails in a user's inbox |

`MAX_LINE_LENGTH` is also defined in config.py as a global constant. It is not
meant to be tuned: it reflects the physical memory limits of the device.
Input lines longer than this are cut off.
The gameplay controller rejects the whole overlong line rather than executing
a truncated command or password prefix.

> **Change the defaults before running a private MUD.** The default
> `AP_PASSWORD`, `ADMIN_NAME`, `ADMIN_PASSWORD` and `PASSWORD_SALT` are public
> on GitHub. That is fine for an open "come find it" MUD, but anyone who knows
> the project can join the wifi and log in as the admin (user 1). Admins who
> want to control who joins should change all four in config.py before the
> first boot. The admin account and the password hashes are created with
> these values on first boot, so changing the salt later makes existing
> passwords invalid.

## Telnet handling
- Telnet negotiation sequences (IAC) sent by clients are filtered out of the
  input.
- Both CRLF and LF line endings are accepted and backspace is handled.
  Input is decoded as UTF-8 (so `äöå` and the like work); control characters
  and invalid UTF-8 byte sequences are dropped. A backspace removes a whole
  character, not a single byte.
- `MAX_LINE_LENGTH` is measured in bytes (a UTF-8 character can take up to 4
  bytes). `MAX_NAME_LENGTH`, `MAX_DESCRIPTION_LENGTH` and `MAX_TEXT_LENGTH` are measured in characters.
- `/connect <name>` asks for the password on a separate prompt.
  `/connect <name> <password>` remains valid with visible inline input.
  Password masking is not required for this version.
- Every client has its own outgoing buffer. Output is written from the event
  loop without blocking, so one slow client can never stall the MUD.
- Connections are long-lived (unlike an HTTP request/response), and the server
  must be able to push text to any client at any time (say, emote, arrivals,
  pages, etc.).

## Sessions
Online presence is managed by controllers in memory, separate from persistent
models, and is never written to disk. Transport buffers remain in the telnet
module; controller session records refer to their connection. A session
holds:
- the connection and its input/output buffers
- the user_id (or the generated guest name)
- the current room_id
- the time of the last activity (for `IDLE_TIMEOUT`)

Rules:
- A user can only be online once. When a user logs in while already online,
  the existing session is told it was replaced and is disconnected, and the
  new session takes over.
- Every session enters the world in room 1, the permanently public global home.
- When a player enters or leaves a room, the other players in that room are
  notified ("peter arrives from the south", "peter leaves north").
- Banned users can not log in. When a user is banned, any active session of
  that user is disconnected.
- When a session disconnects or times out, it is removed from memory and the
  room is notified.

## Notifications
Notifications use direct controller calls and the session controller's live
session collection. With `MAX_CLIENTS` defaulting to 6, selecting recipients
by scanning that collection is sufficient. There is no channels module,
subscription registry or event bus; room membership comes from each session's
current `room_id`.

`controllers/notification_controller.py` selects recipients and uses
`views/notification_view.py` to format notification text. It queues output
through the telnet module's existing per-client buffers. Models never send
notifications themselves.

Delivery operations:
- `send_to_session(session, message)`: direct delivery to a player or guest.
- `send_to_user(user_id, message)`: resolve the user's live session and deliver
  to it. Report when the user is offline; do not queue transient notifications
  for later. Persistent mail remains a separate feature.
- `send_to_room(room_id, message, exclude_session=None)`: deliver to live user
  and guest sessions currently in that room, optionally excluding the actor.
- `send_to_all(message)`: deliver to all live player and guest sessions.

Only active gameplay sessions are recipients, not connections waiting to log
in or connections already closing. Failed delivery to one recipient does not
prevent delivery to others. Notifications have no separate persistent queue.

### Movement and presence
The movement controller first validates the destination and permission to
enter. Once the move can succeed, it queues a departure notification for the
old room excluding the mover, updates the mover's session location, then
queues an arrival notification for the new room excluding the mover. The
mover receives the destination's room description. Perform this sequence in
one controller turn so later commands see the updated location.

Failed moves emit neither departure nor arrival notifications. Directional
movement uses text such as "Peter leaves north" and, when the return direction
is known, "Peter arrives from the south". Teleports use suitable non-directional
text. A move to the current room does not announce a departure and arrival.

Joining the world announces arrival. A disconnect or idle timeout removes the
session and announces departure to the remaining players in its last room.
These session changes and notifications do not mark database models dirty.

### Chat and other messages
The chat controller routes `/say` and `/emote` to the sender's current room,
including the sender as confirmation. Whispers target a session in the same
room; pages target a session anywhere, including guest sessions. Controllers
validate recipients and permissions before requesting delivery. Admin
announcements use global delivery. Sending mail can trigger a direct new-mail
notification if the recipient is online; the mail model mutation, rather
than the notification, marks mail data dirty.

### Display and implementation scope
Unsolicited text starts on a fresh line and is followed by a new `> ` prompt
for sessions accepting commands. Keep the existing plain UTF-8 presentation;
restoring partially typed input with cursor control is deferred. Do not insert
the normal command prompt into a login or password-entry exchange.

The `add-core-boot-telnet` change provides controller-driven buffered output
between input lines. Session selection, notification controllers/views and
room/chat behavior are added with the later session and gameplay features.

## Data
Data for the MUD is stored in /data (/target/data in this repo).
All ids and all references to ids are numbers in memory and JSON values.
Mail's JSON object keys are decimal strings on disk (required by JSON) and
converted to numeric user ids when loaded.
There are 3 different files:

users.json - contains the user data, including usernames, passwords, and
admin status. The top level is an array of users.

```
[
  {
    user_id: number // unique identifier for the user. the first admin is always user_id 1
    name: string
    password: string // sha256 hex digest of PASSWORD_SALT + password
    admin: boolean
    home_room_id: number // the room_id of the user's home room
    banned: boolean // whether the user is banned from the MUD
  }
]
```

rooms.json - contains the room data, including room descriptions, exits, and
items. The top level is an array of rooms.

```
[
  {
    room_id: number // unique identifier for the room
    owner_id: number // the user_id of the user who owns this room (and all items in it)
    name: string
    description: string
    private: boolean // only the owner and admins can enter a private room. room 1 is always public.
    unlocked_if: [[variable_name: string, operator: "equals" | "more_than" | "less_than", value: number | string]]
    exits: {
      // to_room_id is the room_id of the room that this exit leads to.
      // name is the name of the exit, this is what the user sees when they look around in the room.
      // description is the description of the exit, this is what the user sees when they look at the exit.
      // locked is a boolean that indicates whether the exit is locked or not. if the exit is locked, nobody can use it to navigate to the other room. only the room owner can lock/unlock it.
      // activation_text is the text that is displayed to the user when they use the exit.
      north?: { to_room_id: number, name: string, description: string, locked: boolean, activation_text: string }
      east?: { to_room_id: number, name: string, description: string, locked: boolean, activation_text: string }
      south?: { to_room_id: number, name: string, description: string, locked: boolean, activation_text: string }
      west?: { to_room_id: number, name: string, description: string, locked: boolean, activation_text: string }
      up?: { to_room_id: number, name: string, description: string, locked: boolean, activation_text: string }
      down?: { to_room_id: number, name: string, description: string, locked: boolean, activation_text: string }
    }
    items: [
      {
        id: number, // unique within this room only
        name: string,
        description: string,
        visible_if: [[variable_name: string, operator: "equals" | "more_than" | "less_than", value: number | string]],
        creature?: true, // present only when this item is a creature
        interactions: [{action: string, flavor_text: string, available_if: [[variable_name: string, operator: "equals" | "more_than" | "less_than", value: number | string]], teleport_to_room_id?: number, set_variable?: [variable_name: string, value: number | string]}],
        cron_jobs?: [
          {
            id: number, // unique within this item only
            name: string,
            interval_seconds: number, // positive
            chat_out?: string,
            emote?: string,
            set_variable?: [variable_name: string, value: number | string]
          }
        ]
      }
    ]
  }
]
```

Item ids are unique within their room. When an item is moved to another room,
it is removed from the old room and re-created in the new room with a new id.
`creature` is optional and, when present, must be `true`. `cron_jobs` is
optional and omitted when an item has no cron jobs. Each cron job has a positive
`interval_seconds` value; `chat_out` and `emote` are independently optional.
Condition arrays are normalized to empty arrays on startup. All entries in an
`*_if` array must match. Variable names are 1-15 character lowercase identifiers
that start with a letter and use letters, digits, and single underscores. They
are displayed with underscores replaced by spaces and the first letter
capitalized. Stored numeric values are 0-100; numeric effects are signed deltas
clamped to that range, while string effects replace values. Quoted builder values
are always strings, including `"01"`; unquoted integer tokens are numeric.
Session variables are kept per player and room owner, are limited to six per
owner, and clear on disconnect or restart. Global home and every user's personal
home are always public and cannot have `unlocked_if` rules.

mail.json - contains the inbox of every user. The top level is an object keyed
by user_id; each inbox is an array of at most `MAX_MAILS` mails.

```
{
  [user_id]: [{ from_user_id: number, title: string, message: string }]
}
```

## Persistence
The authoritative state is held in shared, application-lifetime model
instances. Controllers invoke model operations; models update their data and
mark the affected file dirty. Commands never write to disk directly.

The users, rooms and mail models each own their file's dirty flag. The items
model changes the rooms model's nested items and marks that shared rooms flag
dirty. Reading data or changing online presence does not mark any file dirty.

Every `SAVE_INTERVAL` seconds (default 60), an application controller invokes
the models' save-if-dirty operations from an event-loop tick. `/save` invokes
the same operations immediately. Models own serialization and clear their
flag only after a successful save. The telnet module only supplies the tick;
it neither knows the database filenames nor inspects dirty flags. Files that
are not dirty are never overwritten, and no comparison copy is held in RAM.
Session data (who is online, where they are) is never part of this state.

Writing a file:
- The data is streamed with `json.dump(obj, f)`, never built as one big string
  with `json.dumps`, to avoid a large memory spike.
- It is written to a temporary file first (e.g. `rooms.json.tmp`) and then
  renamed over the real file after successful close. This protects individual
  files under the filesystem's guarantees, not all three as one transaction.
  Cross-file inconsistencies after interrupted saves stop boot with diagnostics
  and preserve the files for admin recovery.
- If writing fails, the dirty flag stays set so the next interval retries.

## Memory
The Pico 2 W has 520 KB of SRAM, of which roughly 300–400 KB is available as
MicroPython heap once wifi is up (to be verified with `gc.mem_free()`). All
state lives in RAM, so the limits in config.py are chosen to keep the
worst case bounded:
- `MAX_USERS` (default 15) caps the total amount of rooms, items and mail.
- Short labels (room, exit, item and action names and mail titles) are
  limited to `MAX_NAME_LENGTH` (default 60). Room and item descriptions use
  `MAX_DESCRIPTION_LENGTH` (600). Activation and flavor texts, chat and mail
  messages use `MAX_TEXT_LENGTH` (250).
- Commands that create data (`/dig`, `/create`, `/interaction add`,
  `/mail send`, `/user create`) are refused with a message when
  `gc.mem_free()` is below `MIN_FREE_MEMORY` (after a `gc.collect()`).
- `gc.collect()` runs regularly from the event loop.
- Code should be precompiled to `.mpy` with `mpy-cross` where possible, so
  the Pico does not have to compile source files in RAM at import.

## Mail
Every user has an inbox of at most `MAX_MAILS` (default 10) mails. Users can
only read and delete their own mail; admins can not read other users' mail.
When a recipient's inbox is full, new mail to that user is refused and the
sender is told the inbox is full. Guests can not send or receive mail.
If the recipient is online, they get a notification that new mail arrived.

## Default rooms
From the get-go (when there is no users.json or rooms.json yet) a base
users.json and rooms.json should be created containing an initial admin record
and the admin's home room. An empty mail.json is created as well.

The username and password of the admin should be whatever is configured in the
/config.py (/target/config.py) file, this file also contains the salt used for
hashing the password.
The initial admin's home room is room 1: a simple room with a description and
no items or exits. Room 1 remains the global home, permanently public and
undeletable, even if the admin later chooses a different personal home.

Any user entering the MUD will always land in room 1 first
from where they can navigate around the admin's property.

Typing `/teleport global home` brings the user back.

## Login
After logging in either as a user or a guest, the user receives a welcome
(programmed in the /config.py) as well as basic instructions on
how they can navigate around the MUD, how to teleport to their own room (or any
room id) and how to return to the global home.

## Commands
The commands come from LambdaMOO. The names stay close to the MOO originals,
but they are adjusted to fit the PICO MUD data model: rooms, exits and items
with interactions, and no general object programming. Every command starts
with `/`. Input without a leading `/` is treated as `/say`, and the LambdaMOO
shortcuts `"` (say) and `:` (emote) also work. Commands are case-insensitive.

Arguments in `[brackets]` are optional, `<angle>` arguments are required.
`<dir>` is one of `north|east|south|west|up|down`, with the short forms
`n|e|s|w|u|d`.

Permission levels:
- **G**: guest, and everyone else
- **U**: logged-in user
- **O**: user who owns the current room (admins count as owners everywhere)
- **A**: admin only

### Session & account
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/connect <name> <password>` | `connect` | G | Log in as a user. `/login` works as an alias. If the user is already online, the old session is disconnected. |
| `/connect <name>` | `connect` | G | Ask for the password on a separate prompt; masking is not required. `/login <name>` also works. |
| `/connect guest` | `connect guest` | G | Continue as an anonymous guest (`guest-1`, `guest-2`, ...). |
| `/quit` | `@quit` | G | Disconnect from the MUD. |
| `/password <old> <new>` | `@password` | U | Change your own password. |
| `/help [command]` | `help` | G | Show focused help. Topics: `tutorial`, `user`, `movement`, `building`, and `programming` (interactions, habbits, and variables). Admins also see `admin` for world management. |
| `/who` | `@who` / `who` | G | List connected players and the room each one is in. |
| `/whoami` | `@whoami`-style | G | Show your name, user id, admin status and home room. |

### Looking around
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/look` (`/l`) | `look` | G | Show the current room: name, description, exits, items and players present. |
| `/look at <item\|dir\|player>` | `look <thing>` | G | Show the description of an item, exit or player. For items, also list the actions they support. |
| `/examine <item\|dir>` (`/ex`) | `@examine` | G | Show technical details: ids, owner, locked state, and interactions (the owner also sees teleport targets). |
| `/exits` | `@exits` | G | List the exits of the current room with their names and locked state. |
| `/rooms [user]` | `@audit` | U | List rooms by id and name for yourself or another user. Private rooms are hidden from non-owners. |
| `/items [user]` | `@audit` | U | List the items you (or another user) own, and the rooms they are placed in. |

### Moving
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/go <dir>` or `/<dir>` (`/n`, `/e`, ...) | `go` / direction verbs | G | Take an exit and show its `activation_text`. Locked exits block everyone; private destinations allow their owner and admins. |
| `/teleport home` / `/teleport to home` (`/home`) | `home` | U | Go to your own home room. |
| `/teleport global home` / `/teleport to global home` | `@join`-style | G | Go back to room 1, the permanently public global home. |
| `/teleport to <room_id>` | `@go` | G | Go directly to a room by id. Private rooms require ownership or admin access. |
| `/join <player>` | `@join` | G | Go to another live player's room if accessible under the same privacy rules. |

### Communication
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/say <text>` (`"text`) | `say` | G | Say something to everyone in the room. |
| `/emote <text>` (`:text`) | `emote` | G | Act out an action, for example `:waves` shows `peter waves`. |
| `/whisper <player> <text>` | `whisper` | G | Send a private message to a player in the same room. |
| `/page <player> <text>` | `page` | G | Send a private message to a player anywhere in the MUD. |
| `/shout <text>` | `@shout` (wizard) | A | Broadcast a message to every connected player. |

### Mail
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/mail` | `@mail` | U | List your inbox: number, sender and title of each mail. |
| `/mail read <number>` | `@read` | U | Read one of your mails. |
| `/mail send <user> <title> = <message>` | `@send` | U | Send a mail. Refused when the recipient's inbox holds `MAX_MAILS` mails, when the title exceeds `MAX_NAME_LENGTH` or the message exceeds `MAX_TEXT_LENGTH`, or when memory is low. |
| `/mail delete <number>` | `@rmmail` | U | Delete one of your mails. |

### Interacting with items
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/<action> <item>` | object verbs (`push button`) | G | Show static flavor text and optionally teleport the actor if the target exists and is accessible. Cross-owner public targets are allowed; private targets require ownership or admin access. Items never change as a result. |
| `/use <item>` | generic verb | G | Run the item's first interaction, or list its actions if it has more than one. |

Actions can never conflict with existing commands: every command name and
alias listed in this section (e.g. `look`, `go`, `mail`, `n`, `use`) is
reserved, and creating an interaction with a reserved action name is refused.

### Building: rooms
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/dig <dir> <room name>` | `@dig` | O | Create a new room that you own and connect it to the current room with a two-way exit in `<dir>`, using the opposite direction on the way back. You can only dig from rooms you own, and only up to `MAX_ROOMS_PER_USER` rooms. Refused when memory is low. |
| `/dig <dir> to <room_id>` | `@dig exit to #room` | O | Link two rooms with the same owner, adding the opposite return exit. Refuse links between different owners' rooms. |
| `/undig <dir>` | `@recycle` exit | O | Remove an exit from the current room. |
| `/rename here <name>` | `@rename here` | O | Rename the current room. |
| `/describe here <text>` | `@describe here` | O | Set the description of the current room. |
| `/private [on\|off]` | lock room | O | Toggle whether only the owner and admins can enter the room. Room 1 must remain public. |
| `/room-unlock-rules add\|remove <variable> <equals\|more_than\|less_than> <value>` | - | O | Add or remove a room-entry variable condition. Global home and personal homes cannot have rules. |
| `/room-unlock-rules clear` | - | O | Clear all room-entry variable conditions. |
| `/sethome` | `@sethome` | O | Make the current room your home room. It must be a room you own. |
| `/destroy room <room_id>` | `@recycle` | O | Delete a permitted room. Exits pointing to it are removed, and players inside are sent to room 1. Room 1 and any user's current home cannot be deleted. |

### Building: exits
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/rename <dir> <name>` | `@rename` exit | O | Set the name players see for an exit, for example `a creaky door`. |
| `/describe <dir> <text>` | `@describe` exit | O | Set the text shown by `/look at <dir>`. |
| `/message <dir> <text>` | `@leave`/`@oleave` msgs | O | Set the exit's `activation_text`, for example `You squeeze through the gap...`. |
| `/lock <dir>` | `@lock` | O | Lock an exit so it cannot be used. |
| `/unlock <dir>` | `@unlock` | O | Unlock an exit. |

### Building: items
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/create <item name>` | `@create` | O | Create a new item in the current room (up to `MAX_ITEMS_PER_ROOM`). Refused when memory is low. |
| `/item set <item> visible add\|remove <variable> <condition> <value>` | - | O | Add or remove item/creature visibility conditions. |
| `/item set <item> visible clear` | - | O | Clear item/creature visibility conditions. |
| `/rename <item> <name>` | `@rename` | O | Rename one of your items. |
| `/describe <item> <text>` | `@describe` | O | Set an item's description. |
| `/interaction add <item> <action> <flavor text>` | `@verb` | O | Add an interaction (up to `MAX_INTERACTIONS_PER_ITEM`), for example `/interaction add lever pull The floor creaks...`. Refused if `<action>` is a reserved command name, or when memory is low. |
| `/interaction teleport <item> <action> <room_id>` | `@verb` + `move()` | O | Make an existing interaction teleport the player to `<room_id>`. Use `none` to clear it. |
| `/interaction remove <item> <action>` | `@rmverb` | O | Remove an interaction. |
| `/interaction require <item> <action> add\|remove <variable> <condition> <value>` | - | O | Add or remove interaction availability conditions. |
| `/interaction require <item> <action> clear` | - | O | Clear interaction availability conditions. |
| `/interaction set <item> <action> <variable> <value>` | - | O | Set an interaction variable effect. |
| `/interaction clear <item> <action>` | - | O | Clear an interaction variable effect. |
| `/interactions <item>` | `@verbs` | G | List an item's actions. The owner also sees flavor texts and targets. |
| `/habbit set <item> <id> <variable> <value>` | - | O | Set a cron job variable effect. |
| `/habbit clear <item> <id>` | - | O | Clear a cron job variable effect. |
| `/move <item> to <room_id>` | `@move` | O | Move one of your items to another room you own. The item is removed and re-created in the target room with a new id. |
| `/destroy <item>` | `@recycle` | O | Delete one of your items. |

### Administration
| Command | MOO origin | Level | Description |
|---|---|---|---|
| `/user create <name> <password> [admin]` | `@make-player` | A | Create a user and their home room. Refused when `MAX_USERS` is reached or memory is low. |
| `/user remove <name>` | `@recycle` player | A | Delete a user together with their rooms, items and mail. User 1 cannot be removed. |
| `/user ban <name>` | `@toad` / `@newt` | A | Ban a user: they are disconnected and can no longer log in. |
| `/user unban <name>` | undo `@newt` | A | Lift a ban. |
| `/user admin <name> [on\|off]` | `@programmer`/wizard bit | A | Grant or revoke admin rights. User 1 always stays an admin. |
| `/user password <name> <new>` | `@newpassword` | A | Reset a user's password. |
| `/users` | `@users`-style | A | List all users with their id, admin flag, banned flag and home room. |
| `/boot <player>` | `@boot` | A | Disconnect a connected player or guest. |
| `/save` | `@dump-database` | A | Run the save check right away instead of waiting for the next `SAVE_INTERVAL`. |
| `/uptime` | `@uptime` | G | Show server uptime, free memory (`gc.mem_free()`), the number of connected players, and the number of users and rooms against their limits. |

## Output formatting
Output is kept simple:
- All output is plain UTF-8 text, so `äöå` and other non-ASCII characters are
  shown as typed. No ANSI colors or cursor control.
- Lines are sent with CRLF (`\r\n`) endings, as telnet expects.
- The server does not wrap text; the client terminal takes care of wrapping.
- A short prompt `> ` is shown after each command's output.
- Room displays have a blank line before the room name and after the player
  list, separating login, movement, teleport and `/look` output.
- A room is shown as its name on the first line, then its description, then a
  line of exits, items and players present, for example:

```
The Great Hall
A huge hall with a vaulted ceiling. Dust dances in the light.
Exits: north (a creaky door), up (a spiral staircase)
Items: lever, sign
Here: peter, guest-2
> 
```

## LED status
The onboard LED shows the state of the Pico:

| Pattern | Meaning |
|---|---|
| 1 blink | Wifi hotspot is up and broadcasting |
| 2 blinks, then stays on | Telnet server is running, all good |
| 3 blinks, repeating | Fatal error (see Error handling) |

## Error handling
Errors in a single command or a single client connection are logged and never
bring down the MUD; the command fails with a message to that user, or the
connection is closed.

When a fatal error occurs (the event loop itself fails), the error and its
traceback are printed to the serial console, the server stops and the LED
blinks 3 times, repeating, until the Pico is reset. The admin can connect the
Pico to a computer and read the logs over serial (e.g. `mpremote connect auto
repl`). There is no automatic reboot or watchdog.

## Networking scope
The Pico only runs the wifi hotspot (with its built-in DHCP) and the telnet
server. There is no DNS server, no captive portal and no HTTP server: this
keeps the event loop focused on telnet. The admin is responsible for giving
players the wifi password and telling them to join the "PICO MUD" wifi and run
`telnet 192.168.4.1 8888`.

The hotspot uses WPA2 (AES/PSK). Encryption is handled entirely by the wifi
chip's firmware, so it costs nothing in the event loop. It is configured once
at boot via `ap.config(ssid=AP_SSID, key=AP_PASSWORD, security=...)`; the exact
security constant for the installed MicroPython version must be verified
during implementation (the reference project uses `security=0`, which is
open). Note that telnet itself is still unencrypted: anyone who knows the wifi
password can in theory sniff traffic, so users should not reuse real
passwords.

## Testing
No unit or integration tests are required for now.

## Deployment
The MVC MUD implementation is in `target/`. Upload its root files
and packages over USB; the development computer can stay on its usual Wi-Fi.

```sh
uvx mpremote connect list
uvx mpremote connect /dev/cu.usbmodem2101 fs cp -r target/models target/modules target/controllers target/views target/main.py :
uvx mpremote connect /dev/cu.usbmodem2101 reset
uvx mpremote connect /dev/cu.usbmodem2101 repl
```

Use the port reported by `connect list`; omit `uvx` if `mpremote` is installed.
Back up device files first. Copy config.py separately only after comparing
customized credentials/settings; never overwrite existing `/data` during upload.
This package upload was verified on a Pico 2 W with MicroPython 1.29.0.
Attach to serial before resetting to capture boot messages. Historical serial
output is not saved to disk. Interrupting the application for serial commands
can stop the hotspot; reset when finished to restart it.

To play, join **PICO MUD** with the configured `AP_PASSWORD` (default
`MultiUserDungeon`), then run `telnet 192.168.4.1 8888`. The pre-login screen
shows the seven-line PICO MUD block-art banner and connection instructions.
Use `/connect admin changeme` for the initial admin or `/connect guest` to
explore; `/connect <name>` prompts for a password. `/help` describes the game
commands. Changes save every 60 seconds or immediately with admin `/save`.

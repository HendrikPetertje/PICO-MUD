# MVC boundaries

Source: the project's MVC decision and `openspec/PROJECT_OUTLINE.md`.
The boot utilities, telnet controller and text view are implemented under
`target/`. Model and notification ownership below describes later features.

## First boot/telnet change

| Location under `target/` | Responsibility |
|---|---|
| `config.py` | One root-level settings file |
| `main.py` | Validate configuration, wire dependencies, start utilities, handle fatal errors |
| `modules/wifi.py` | Access point operations |
| `modules/led.py` | Hardware status patterns |
| `modules/telnet.py` | Socket lifecycle, polling, UTF-8/framing, bounded buffers and event callbacks |
| `controllers/telnet_controller.py` | Application handling of connection events, commands and responses |
| `views/telnet_view.py` | Plain-text formatting with no socket or database access |

The transport receives its controller through dependency injection. It emits
connect, line, rejection, timeout, disconnect and timer events. The controller
chooses a view response and sends it through the transport API. Low-level
socket errors can close a connection immediately and report the disconnect.
No command names or user-facing message templates belong in the transport.

## Later database features

- `models/users.py` owns user records, `users.json` and its dirty flag.
- `models/rooms.py` owns room/exit records and nested item storage, `rooms.json`
  and its dirty flag.
- `models/items.py` owns item/interaction operations over the shared rooms
  data. Item keys are `(room_id, item_id)`. Mutations mark the rooms model
  dirty; items have no duplicate storage, separate file or independent save.
- `models/mail.py` owns inboxes, `mail.json` and its dirty flag.

Share one application-lifetime instance of each model across controllers.
Controllers invoke model operations rather than modifying dictionaries or
flags. Models enforce data invariants; controllers check player permissions.
Controllers also keep online presence and current location outside the
persistent models, so walking, logging in and disconnecting do not trigger saves.

A later application controller uses timer events to call model save-if-dirty
operations every 30 seconds. `/save` uses the same path immediately. Models
stream to a temporary file, replace their own file, and clear the dirty flag
only on success. Failed saves retain the flag. Saving the rooms model writes
rooms and nested items together once.

## Review checklist

- Utilities do not import concrete controllers, views or models.
- Controllers own command dispatch and all application-facing transport calls.
- Views format supplied values and never send data themselves.
- Database state and dirty flags belong to models, not controllers or config.
- The first change instantiates no persistent models and writes no databases.

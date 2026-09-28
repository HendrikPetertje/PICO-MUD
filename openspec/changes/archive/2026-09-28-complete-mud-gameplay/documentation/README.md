# Implementation references

- `command-contract.md`: exhaustive command grammar, aliases and permissions.
- `micropython-data.md`: retrieved JSON/hash source excerpts and device constraints.
- `acceptance.md`: multi-user, ownership, persistence and resource walkthrough.
- `../design.md`: module responsibilities, session transitions, save strategy
  and bounded response delivery.
- `../../../PROJECT_OUTLINE.md`: project-wide goals and latest user decisions.
- `../../archive/2026-09-28-add-core-boot-telnet/documentation/`: verified device,
  transport and deployment notes from the completed base.

Reference source inspected: `openspec/reference-project/messages_controller.py`
keeps messages in RAM and mixes controller/rendering/storage. Reuse only useful
MicroPython patterns; persistent data belongs to the new models.

Target: Pico 2 W, MicroPython 1.29.0 as observed in the previous change.
The USB port can change: discover it before implementation upload. Never copy
an empty repository data directory over an existing live database. Documentation
must distinguish local checks, actual device checks and user confirmations.

## Delivered implementation

See `verification.md` for measured results and remaining user acceptance.
Pure rendering helpers are consolidated in `target/views/game_view.py`, with
the pre-login block-art banner in `target/views/telnet_view.py`. Other module
boundaries follow the design. `/help` is generated from `modules/commands.py`.

USB upload (after backing up existing files and comparing config):

```sh
uvx mpremote connect list
uvx mpremote connect /dev/cu.usbmodem2101 fs cp -r target/models target/modules target/controllers target/views target/main.py :
uvx mpremote connect /dev/cu.usbmodem2101 reset
```

Only copy `target/config.py` separately when its intended changes have been
compared with the device config. Never upload repository data over `/data`.
To back up, copy device `:config.py`, `:main.py` and package directories to a
local backup directory; include `:data` if it exists. Read/exec/copy operations
can interrupt the running app, so reset afterwards. Leave Wi-Fi association
and external telnet checks to the user when the development host needs internet.

## Quick walkthrough

```text
/connect admin changeme
/user create adam pass
/user create bob pass
/help
/users
/save
```

On a second connection:

```text
/connect adam
pass
/home
/dig north "green garden"
/n
/describe here A peaceful garden.
/create "brass lever"
/interaction add "brass lever" pull Whoosh!
/interaction teleport "brass lever" pull 1
/use "brass lever"
/say Hello everyone!
/mail send bob Greetings = Welcome to the world.
```

As Bob use `/mail` then `/mail read 1`. `/whisper` requires the same room;
`/page` works across rooms. Cross-owner exits fail; static item teleports to
public rooms work. `/save` writes dirty models immediately; otherwise wait
30 seconds before power-cycling. Per-file replacement is not a multi-file
transaction: restore a consistent backup if boot detects inconsistent data.

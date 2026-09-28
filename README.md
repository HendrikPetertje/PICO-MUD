# PICO MUD

![PICO MUD screenshot](./demo/screenshot.png)

## About

PICO MUD is a lightweight, text-based multiplayer online game for the Raspberry Pi Pico 2 W. On boot, the Pico creates a WPA2-protected Wi-Fi hotspot and runs a telnet server. Players join the hotspot and connect to the game at `192.168.4.1:8888`.

Guests can explore public rooms and interact with items. Registered players can build rooms, exits, and items, send mail, and chat with other players. The game stores its world data on the Pico.

The MicroPython application is in `target/`. Its contents become the filesystem root of the Pico.

## Installation

### Requirements

- Raspberry Pi Pico 2 W
- MicroPython for the Pico 2 W (verified with MicroPython 1.29.0)
- A USB data cable
- [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html) or `uvx mpremote`
- A telnet client

Before the first boot, review `target/config.py`. Change `AP_PASSWORD`, `ADMIN_NAME`, `ADMIN_PASSWORD`, and `PASSWORD_SALT` when running a private MUD. The defaults are public, and changing the salt after first boot invalidates existing password hashes.

Connect the Pico by USB, identify its serial port, then upload the application:

```sh
uvx mpremote connect list
uvx mpremote connect <serial-port> fs cp -r target/models target/modules target/controllers target/views target/main.py :
uvx mpremote connect <serial-port> reset
```

Copy `target/config.py` separately after comparing it with the configuration already on the device. Do not overwrite the Pico's `/data` directory, which holds the saved world.

After restarting the Pico, join the configured Wi-Fi network, then connect:

```sh
telnet 192.168.4.1 8888
```

Some telnet clients perform DNS lookups and negotiate telnet capabilities when connecting. This may take 15-20 seconds; after the connection is established, the rest of the session should be responsive.

Use `/connect admin changeme` for the default administrator, or `/connect guest` to explore without an account.

## Commands

Every command begins with `/` and is case-insensitive. Plain text is sent to the current room as `/say`; `"text` and `:text` are shortcuts for saying and emoting. Use `/help` to list all commands, or `/help <command>` for detailed help.

| Command | Description |
| --- | --- |
| `/connect guest` | Enter as an anonymous guest. |
| `/connect <name>` | Log in and enter the password at the next prompt. |
| `/help [command]` | List commands or show detailed help for one command. |
| `/look` | Show the current room, its exits, items, creatures, and players. |
| `/go <direction>` | Take an exit. Short forms such as `/n` and `/s` work. |
| `/who` | List connected players. |
| `/say <text>` | Speak to everyone in the current room. |
| `/emote <text>` | Perform an action in the current room. |
| `/whisper <player> <text>` | Send a private message to a player in the same room. |
| `/page <player> <text>` | Send a private message to any connected player. |
| `/mail` | List your mail. |
| `/mail send <user> <title> = <message>` | Send mail to a registered user. |
| `/dig <direction> <room name>` | Create a connected room you own. |
| `/create <item name>` | Create an item in a room you own. |
| `/creature <item> [on|off]` | Classify an item as a creature. |
| `/habbit add <item> <seconds> <name>` | Add timed activity to an item or creature. |
| `/habbit edit <item> <id> <field> <value>` | Edit a habbit's interval, name, chat, or emote. |
| `/habbits <item>` | List an item's timed activity. |
| `/interaction add <item> <action> <text>` | Add an action to an item. |
| `/user create <name> <password>` | Create a user. Administrator only. |
| `/save` | Save changed world data immediately. Administrator only. |
| `/quit` | Disconnect from the MUD. |

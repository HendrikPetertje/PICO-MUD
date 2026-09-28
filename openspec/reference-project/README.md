# Peva Gumstick Wifi Pub

A minimal local chat room running entirely on a Raspberry Pi Pico W2 via MicroPython.

No internet required. No server. Just a Pi, a WiFi radio, and a browser.

## What it does

- Creates an open WiFi network called `PevaPub`
- Triggers the captive portal popup (that login to this wifi hotspot popup you get on airport wifi) automatically when a device connects
- Serves a chat UI at `http://192.168.4.1/`
- Stores the last 10 messages in RAM
- Polls for new messages every 3 seconds
- Handles multiple connected clients simultaneously via a non-blocking event loop
- Blinks the onboard LED to indicate status

## LED status

| Pattern | Meaning |
|---|---|
| 1 blink | AP is up and broadcasting |
| 2 blinks → stays on | HTTP server running, all good |
| 3 blinks repeating | Fatal server error |

## File layout

```
main.py      — boot script: sets up AP, DNS, and HTTP server
dns.py       — minimal UDP DNS server (answers all queries with Pi's IP)
server.py    — non-blocking HTTP server (GET /, GET /messages, POST /messages)
http/index.html   — chat UI (vanilla JS, liquid glass design, no dependencies)
```

## Deploying to the Pico

You need [Thonny](https://thonny.org/) or [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html).

### With Thonny

1. Open the **Files** panel (View → Files).
2. Right-click each file in the left pane → **Upload to /**.
3. Upload: `main.py`, `dns.py`, `server.py`, `index.html`.
4. Reboot the Pico via the reset button or by power-cycling it.

### With mpremote

```sh
pip install mpremote

# Copy all files to the Pico root
mpremote cp main.py dns.py server.py index.html :

# Reset and watch logs
mpremote reset
mpremote connect auto repl
```

## Connecting

1. Join the `PevaPub` WiFi network on your phone or laptop (no password).
2. The captive portal browser should pop up automatically.
3. If it doesn't, open `http://192.168.4.1/` manually in your browser.
4. Enter a name and start chatting.

> Your username is saved in `localStorage` so you don't have to retype it.

## Configuration

Edit the top of `main.py` and `server.py` to change settings:

| Variable | Default | Description |
|---|---|---|
| `AP_SSID` | `"PevaPub"` | WiFi network name |
| `AP_PASSWORD` | `""` | Empty = open network |
| `MAX_MESSAGES` | `20` | Messages kept in RAM |
| `MAX_USERNAME` | `10` | Max username length |
| `MAX_MESSAGE` | `250` | Max message length |

## Caveats

- **Messages are in RAM** — lost on reboot.
- **No persistence** — there is no filesystem-based message log.
- **DNS redirects everything to the Pi** — any domain typed in a browser will point here, which is intentional for captive portal behaviour.

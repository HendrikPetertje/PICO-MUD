---
title: "MicroPython network.WLAN (AP mode) notes for Pico 2 W"
source: "https://github.com/micropython/micropython/blob/master/docs/library/network.WLAN.rst ; https://github.com/micropython/micropython/blob/master/docs/rp2/quickref.rst"
created: 2026-09-27
description: "Access point setup, config parameters and WPA2 security for the rp2/cyw43 port"
tags:
  - "tool-context7"
---

# network.WLAN access point on rp2 (Pico W / Pico 2 W)

## From the official docs (context7, MicroPython master)

rp2 quickref:
```python
import network
ap = network.WLAN(network.WLAN.IF_AP) # create access-point interface
ap.config(ssid='RP2-AP')              # set the SSID of the access point
ap.config(max_clients=10)             # set how many clients can connect to the network
ap.active(True)                       # activate the interface
```

`WLAN.config(param=value, ...)`: set params as keywords, query one at a time
as a string (`ap.config('ssid')`). Relevant params:
- `ssid` (str): AP name
- `channel` (int)
- `hidden` (bool)
- `security` (enum): "Security protocol supported (see module constants)"
- `key` (str): access key (password)
- `txpower`, `pm`

## Source and device verification (2026-09-28)

Connected board: Raspberry Pi Pico 2 W, RP2350, MicroPython v1.29.0 dated
2026-08-24. USB port during implementation: `/dev/cu.usbmodem2101`.

The reference project establishes the AP/LED pattern but uses `security=0`.
Context7 returned WiPy-specific examples for the security lookup, so the
CYW43 implementation was checked directly:

- https://raw.githubusercontent.com/micropython/micropython/v1.26.0/extmod/network_cyw43.c
- https://raw.githubusercontent.com/georgerobotics/cyw43-driver/main/src/cyw43_ll.h

The first source is version-pinned to v1.26.0; the second is a moving upstream
header retrieved on 2026-09-28. These relevant source excerpts are preserved:

```c
case MP_QSTR_security: {
    cyw43_wifi_ap_set_auth(self->cyw, mp_obj_get_int(e->value));
    cycle_active = true;
    break;
}
case MP_QSTR_key:
case MP_QSTR_password: {
    size_t len;
    const char *str = mp_obj_str_get_data(e->value, &len);
    cyw43_wifi_ap_set_password(self->cyw, len, (const uint8_t *)str);
    cycle_active = true;
    break;
}
```

```c
#define CYW43_AUTH_FLAG_AES_ENABLED              0x0004
#define CYW43_AUTH_FLAG_WPA2_SECURITY        0x00400000
#define CYW43_AUTH_WPA2_AES_PSK      (CYW43_AUTH_FLAG_WPA2_SECURITY | CYW43_AUTH_FLAG_AES_ENABLED)
```

The implementation explicitly sets `password=AP_PASSWORD,
security=0x00400004` before enabling the AP. On the connected v1.29.0 board,
startup succeeded, `ap.config('security')` returned `0x400004`, and
`ap.ifconfig()[0]` returned `192.168.4.1`. Correct/wrong-password association
and DHCP on an external client still need user confirmation.

## Compatibility notes
- The reference project uses
  `ap.config(ssid=AP_SSID, password=AP_PASSWORD, security=0)` for an OPEN
  network. `security=0` = open.
- On cyw43, WPA2 needs a key of 8-63 chars. The cyw43 auth constant for
  WPA2-AES-PSK is `0x00400004` (CYW43_AUTH_WPA2_AES_PSK). AP password and
  security are independent settings; do not assume supplying a password
  changes the authentication mode. The automatic choice in station `connect`
  is a different API.
- Verify after boot: `print(ap.config('security'))` and try joining with a
  wrong password (must fail).
- The default AP IP on cyw43 is 192.168.4.1 (`ap.ifconfig()[0]`); DHCP for
  clients is built in.
- AP association-limit support varies with firmware. `MAX_CLIENTS` is enforced
  by the telnet server, not passed to WLAN configuration.

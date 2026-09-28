import network
import time


AP_IP = "192.168.4.1"
# CYW43_AUTH_WPA2_AES_PSK: WPA2 security (0x00400000) | AES (0x0004).
# Unlike station connect(), AP config keeps password and security separate.
WPA2_AES_PSK = 0x00400004
STARTUP_TIMEOUT_MS = 10000


def start_ap(ssid, password):
    ap = network.WLAN(network.WLAN.IF_AP)
    ap.active(False)
    try:
        ap.config(ssid=ssid, password=password, security=WPA2_AES_PSK)
        started = time.ticks_ms()
        ap.active(True)
        while not ap.active():
            if time.ticks_diff(time.ticks_ms(), started) >= STARTUP_TIMEOUT_MS:
                raise RuntimeError("Wi-Fi access point startup timed out")
            time.sleep_ms(100)
        if time.ticks_diff(time.ticks_ms(), started) >= STARTUP_TIMEOUT_MS:
            raise RuntimeError("Wi-Fi access point startup timed out")

        if ap.ifconfig()[0] != AP_IP:
            ap.ifconfig((AP_IP, "255.255.255.0", AP_IP, AP_IP))
        if ap.ifconfig()[0] != AP_IP:
            raise RuntimeError("Wi-Fi access point must use " + AP_IP)
        if ap.config("security") != WPA2_AES_PSK:
            raise RuntimeError("Wi-Fi access point must use WPA2 AES")

        print("Wi-Fi hotspot:", ssid, "at", AP_IP, "(WPA2 AES)")
        return ap
    except BaseException:
        ap.active(False)
        raise

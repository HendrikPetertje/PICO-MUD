import network
import time
import _thread
from machine import Pin
from dns import DNSServer
from server import HTTPServer
from messages_controller import MessagesController
from games_controller import GamesController
from square_controller import SquareController

# --- Config ---
AP_SSID = "PevaPub"
AP_PASSWORD = ""  # open network

# --- Onboard LED ---
led = Pin("LED", Pin.OUT)


def blink(times, on_ms=120, off_ms=120):
    led.off()
    for i in range(times):
        led.on()
        time.sleep_ms(on_ms)
        led.off()
        if i < times - 1:
            time.sleep_ms(off_ms)


def setup_ap():
    ap = network.WLAN(network.WLAN.IF_AP)
    ap.active(True)
    ap.config(ssid=AP_SSID, password=AP_PASSWORD, security=0)
    for _ in range(20):
        if ap.active():
            break
        time.sleep(0.5)
    print(f"AP up: {ap.ifconfig()}")
    return ap


def main():
    ap = setup_ap()
    blink(1)  # AP is up

    ip = ap.ifconfig()[0]
    dns = DNSServer(ip)
    messages = MessagesController()
    games = GamesController()
    square = SquareController()
    http = HTTPServer(messages, games, square)
    print(f"DNS  listening on {ip}:53")
    print(f"HTTP listening on {ip}:80")
    print(f"Visit http://{ip}/ after connecting to '{AP_SSID}'")

    _thread.start_new_thread(dns.run, ())

    blink(2)   # everything ready
    led.on()   # stay on

    try:
        http.run()
    except Exception as e:
        print("Fatal server error:", e)
        led.off()
        while True:
            blink(3, on_ms=100, off_ms=100)
            time.sleep(1)


main()

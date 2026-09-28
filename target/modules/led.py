import time
from machine import Pin


_led = Pin("LED", Pin.OUT)


def on():
    _led.on()


def off():
    _led.off()


def blink(times, on_ms=120, off_ms=120):
    _led.off()
    for i in range(times):
        _led.on()
        time.sleep_ms(on_ms)
        _led.off()
        if i < times - 1:
            time.sleep_ms(off_ms)


def fatal_loop():
    while True:
        blink(3, on_ms=100, off_ms=100)
        time.sleep_ms(1000)

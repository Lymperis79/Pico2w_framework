from machine import Pin
import time
from config import app
from core.logging import log

class LEDIndicator:
    def __init__(self, pin=None):
        # Pico W / Pico 2 W: use "LED" alias (routes through CYW43439 wireless chip)
        # Original Pico: use GPIO 25
        try:
            if pin is None:
                self.led = Pin("LED", Pin.OUT)
            else:
                self.led = Pin(pin, Pin.OUT)
            log('LED initialized on pin: LED (Pico W/2W)')
        except Exception:
            try:
                self.led = Pin(25, Pin.OUT)
                log('LED initialized on pin: 25 (original Pico)')
            except Exception as e:
                log('LED init failed: ' + str(e))
                self.led = None

    def on(self):
        if self.led:
            self.led.value(1)

    def off(self):
        if self.led:
            self.led.value(0)

    def blink(self, duration_ms=None):
        if self.led is None:
            return
        if duration_ms is None:
            duration_ms = app.LED_BLINK_MS
        try:
            self.led.value(1)
            time.sleep_ms(duration_ms)
            self.led.value(0)
        except Exception as e:
            log('LED blink error: ' + str(e))

    def heartbeat(self):
        if self.led is None:
            return
        try:
            self.led.value(1)
            time.sleep_ms(30)
            self.led.value(0)
            time.sleep_ms(50)
            self.led.value(1)
            time.sleep_ms(30)
            self.led.value(0)
        except Exception as e:
            log('LED heartbeat error: ' + str(e))

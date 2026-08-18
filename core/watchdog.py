from machine import WDT

class Watchdog:
    def __init__(self, timeout_ms):
        if timeout_ms > 8388:
            timeout_ms = 8388
        self.wdt = WDT(timeout=timeout_ms)

    def feed(self):
        self.wdt.feed()

from machine import WDT
class Watchdog:
 def __init__(self,timeout_ms): self.wdt=WDT(timeout=timeout_ms)
 def feed(self): self.wdt.feed()

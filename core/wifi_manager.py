import time,machine,network
from config import wifi,app
class WiFiManager:
 def __init__(self,watchdog=None): self.watchdog=watchdog; self.wlan=network.WLAN(network.STA_IF); self.wlan.active(True)
 def is_connected(self): return self.wlan.isconnected()
 def connect(self):
  if self.is_connected(): return True
  for _ in range(app.WIFI_MAX_ATTEMPTS):
   try:self.wlan.disconnect()
   except:pass
   self.wlan.connect(wifi.SSID,wifi.PASSWORD); deadline=time.ticks_add(time.ticks_ms(),app.WIFI_CONNECT_TIMEOUT_S*1000)
   while not self.is_connected() and time.ticks_diff(deadline,time.ticks_ms())>0:
    if self.watchdog:self.watchdog.feed()
    time.sleep_ms(200)
   if self.is_connected(): return True
   time.sleep(app.WIFI_RETRY_DELAY_S)
  machine.reset()
 def reconnect(self): return self.connect()
 def ip_address(self):
  try:return self.wlan.ifconfig()[0]
  except:return '0.0.0.0'
 def rssi(self):
  try:return self.wlan.status('rssi')
  except:return None

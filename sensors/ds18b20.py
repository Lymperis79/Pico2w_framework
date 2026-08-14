import time,onewire,ds18x20
from machine import Pin
from sensors.base import Sensor
class DS18B20(Sensor):
 def __init__(self,c): super().__init__(c['id'],'ds18b20',c.get('location',''),'','onewire_rom'); self.pin=c['pin']; self.init()
 def init(self): self.ow=onewire.OneWire(Pin(self.pin)); self.ds=ds18x20.DS18X20(self.ow); self.roms=self.ds.scan()
 def rom(self,r): return ''.join('{:02x}'.format(x) for x in r) if r else ''
 def read(self):
  try:
   self.roms=self.ds.scan()
   if not self.roms:return []
   self.ds.convert_temp(); time.sleep_ms(750); out=[]
   for r in self.roms:
    try:v=self.ds.read_temp(r); hid=self.rom(r)
    except:v=None; hid=''
    out.append({'name':'temperature','value':v,'unit':'°C','hardware_id':hid,'hardware_id_type':'onewire_rom' if hid else ''})
   return out
  except:self.init(); raise

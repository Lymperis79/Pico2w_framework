import os,ujson as json
from config import app
F='/runtime_config.json'
class ConfigManager:
 def __init__(self): self.data={'sensor_interval_ms':app.SENSOR_INTERVAL_MS}; self.load()
 def load(self):
  try:
   with open(F) as f:self.data.update(json.loads(f.read()))
  except: pass
 def save(self):
  t=F+'.tmp'
  with open(t,'w') as f:f.write(json.dumps(self.data))
  try: os.remove(F)
  except: pass
  os.rename(t,F)
 def sensor_interval_ms(self): return int(self.data['sensor_interval_ms'])
 def apply(self,d):
  if 'sensor_interval_ms' in d:
   v=int(d['sensor_interval_ms'])
   if v<100 or v>86400000: raise ValueError('invalid sensor interval')
   self.data['sensor_interval_ms']=v; self.save()
  return self.data.copy()
 def get(self): return self.data.copy()

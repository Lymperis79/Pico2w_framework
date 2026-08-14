import dht
from machine import Pin
from sensors.base import Sensor
class DHTSensor(Sensor):
 def __init__(self,c,model): super().__init__(c['id'],model,c.get('location','')); self.sensor=(dht.DHT11 if model=='dht11' else dht.DHT22)(Pin(c['pin']))
 def read(self): self.sensor.measure(); return [{'name':'temperature','value':self.sensor.temperature(),'unit':'°C','hardware_id':'','hardware_id_type':''},{'name':'humidity','value':self.sensor.humidity(),'unit':'%','hardware_id':'','hardware_id_type':''}]

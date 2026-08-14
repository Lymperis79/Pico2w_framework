from config.sensors import SENSORS
from sensors.dht import DHTSensor
from sensors.ds18b20 import DS18B20
DRIVERS={'dht11':lambda c:DHTSensor(c,'dht11'),'dht22':lambda c:DHTSensor(c,'dht22'),'ds18b20':DS18B20}
def create_sensors(): return [DRIVERS[c['driver']](c) for c in SENSORS]

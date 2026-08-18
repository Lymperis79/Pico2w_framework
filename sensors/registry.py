from config.sensors import SENSORS
from sensors.dht import DHTSensor
from sensors.ds18b20 import DS18B20
from sensors.bme280 import BME280Sensor
from sensors.aht20 import AHT20Sensor
from sensors.sr04m import SR04MSensor
from sensors.motion import MotionSensor
from sensors.analog_light import AnalogLightSensor
from sensors.bh1750 import BH1750Sensor
from core.logging import log

DRIVERS = {
    'dht11': lambda c: DHTSensor(c, 'dht11'),
    'dht22': lambda c: DHTSensor(c, 'dht22'),
    'ds18b20': DS18B20,
    'bme280': BME280Sensor,
    'aht20': AHT20Sensor,
    'sr04m': SR04MSensor,
    'motion': MotionSensor,
    'analog_light': AnalogLightSensor,
    'bh1750': BH1750Sensor,
}

def create_sensors():
    sensors = []
    for c in SENSORS:
        driver_name = c.get('driver')
        driver = DRIVERS.get(driver_name)
        if driver is None:
            log('Unknown sensor driver: ' + str(driver_name) + ', skipping sensor ' + str(c.get('id')))
            continue
        try:
            sensor = driver(c)
            sensors.append(sensor)
            log('Initialized sensor: ' + str(c.get('id')) + ' (' + str(driver_name) + ')')
        except Exception as e:
            log('Failed to init sensor ' + str(c.get('id')) + ' (' + str(driver_name) + '): ' + str(e))
    return sensors

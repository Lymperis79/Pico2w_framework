import dht, time
from machine import Pin
from sensors.base import Sensor

class DHTSensor(Sensor):
    def __init__(self, c, model):
        super().__init__(c['id'], model, c.get('location', ''), topic=c.get('topic'))
        self.sensor = (dht.DHT11 if model == 'dht11' else dht.DHT22)(Pin(c['pin']))

    def read(self):
        try:
            self.sensor.measure()
            return [
                {'name': 'temperature', 'value': self.sensor.temperature(), 'unit': 'C'},
                {'name': 'humidity', 'value': self.sensor.humidity(), 'unit': '%'}
            ]
        except Exception:
            time.sleep_ms(500)
            self.sensor.measure()
            return [
                {'name': 'temperature', 'value': self.sensor.temperature(), 'unit': 'C'},
                {'name': 'humidity', 'value': self.sensor.humidity(), 'unit': '%'}
            ]

from machine import Pin
from sensors.base import Sensor

class MotionSensor(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'motion', c.get('location', ''), topic=c.get('topic'))
        self.pin = Pin(c['pin'], Pin.IN)
        self._last_state = None

    def read(self):
        val = self.pin.value()
        if val == self._last_state:
            return []
        self._last_state = val
        return [{'name': 'motion', 'value': bool(val), 'unit': 'bool'}]

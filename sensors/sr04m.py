import time
from machine import Pin
from sensors.base import Sensor
from core.logging import log

class SR04MSensor(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'sr04m', c.get('location', ''), topic=c.get('topic'))
        self.trigger = Pin(c['trigger_pin'], Pin.OUT)
        self.echo = Pin(c['echo_pin'], Pin.IN)
        self.trigger.value(0)
        self.max_distance = c.get('max_distance_cm', 400)
        self.timeout_us = int(self.max_distance * 2 / 0.0343) + 1000

    def read(self):
        self.trigger.value(0)
        time.sleep_us(5)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)

        start_wait = time.ticks_us()
        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), start_wait) > self.timeout_us:
                log('SR04M timeout waiting for echo start')
                return [{'name': 'distance', 'value': None, 'unit': 'cm'}]

        start = time.ticks_us()
        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), start) > self.timeout_us:
                log('SR04M timeout waiting for echo end')
                return [{'name': 'distance', 'value': None, 'unit': 'cm'}]

        end = time.ticks_us()
        duration = time.ticks_diff(end, start)
        distance = (duration * 0.0343) / 2.0
        return [{'name': 'distance', 'value': round(distance, 1), 'unit': 'cm'}]

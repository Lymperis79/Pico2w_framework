import time
from machine import Pin, I2C
from sensors.base import Sensor
from core.logging import log

class _AHT20:
    def __init__(self, i2c, addr=0x38):
        self.i2c = i2c
        self.addr = addr
        self._init()

    def _init(self):
        self.i2c.writeto(self.addr, b'\xBA')
        time.sleep_ms(20)
        self.i2c.writeto(self.addr, b'\xBE\x08\x00')
        time.sleep_ms(10)
        for _ in range(100):
            status = self.i2c.readfrom(self.addr, 1)[0]
            if status & 0x08:
                break
            time.sleep_ms(10)

    def _trigger(self):
        self.i2c.writeto(self.addr, b'\xAC\x33\x00')

    def _status(self):
        return self.i2c.readfrom(self.addr, 1)[0]

    def read(self):
        self._trigger()
        for _ in range(100):
            status = self._status()
            if not (status & 0x80):
                break
            time.sleep_ms(10)
        data = self.i2c.readfrom(self.addr, 7)
        raw_h = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        raw_t = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        h = raw_h * 100.0 / 1048576.0
        t = raw_t * 200.0 / 1048576.0 - 50.0
        return round(t, 2), round(h, 2)


class AHT20Sensor(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'aht20', c.get('location', ''), topic=c.get('topic'))
        bus = c.get('i2c_bus', 0)
        sda = Pin(c.get('sda', 0))
        scl = Pin(c.get('scl', 1))
        freq = c.get('freq', 400000)
        self.i2c = I2C(bus, sda=sda, scl=scl, freq=freq)
        devices = self.i2c.scan()
        if 0x38 not in devices:
            log('AHT20 warning: addr 0x38 not found in scan: ' + str(devices))
        self.sensor = _AHT20(self.i2c)

    def read(self):
        t, h = self.sensor.read()
        return [
            {'name': 'temperature', 'value': t, 'unit': 'C'},
            {'name': 'humidity', 'value': h, 'unit': '%'}
        ]

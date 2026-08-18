import time
from machine import Pin, I2C
from sensors.base import Sensor
from core.logging import log

class _BH1750:
    POWER_DOWN = 0x00
    POWER_ON = 0x01
    RESET = 0x07
    CONT_HRES = 0x10
    CONT_HRES2 = 0x11
    CONT_LRES = 0x13

    def __init__(self, i2c, addr=0x23):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto(addr, bytes([self.POWER_ON]))
        time.sleep_ms(10)
        self.i2c.writeto(addr, bytes([self.CONT_HRES]))
        time.sleep_ms(180)

    def read(self):
        data = self.i2c.readfrom(self.addr, 2)
        raw = (data[0] << 8) | data[1]
        return raw / 1.2


class BH1750Sensor(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'bh1750', c.get('location', ''), topic=c.get('topic'))
        bus = c.get('i2c_bus', 0)
        sda = Pin(c.get('sda', 0))
        scl = Pin(c.get('scl', 1))
        freq = c.get('freq', 400000)
        addr = c.get('addr', 0x23)
        self.i2c = I2C(bus, sda=sda, scl=scl, freq=freq)
        devices = self.i2c.scan()
        if addr not in devices:
            log('BH1750 warning: addr 0x' + '{:02x}'.format(addr) + ' not found in scan: ' + str(devices))
        self.sensor = _BH1750(self.i2c, addr)

    def read(self):
        lux = self.sensor.read()
        return [{'name': 'illuminance', 'value': round(lux, 1), 'unit': 'lx'}]

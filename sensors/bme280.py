import time
from machine import Pin, I2C
from sensors.base import Sensor
from core.logging import log

class _BME280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        self._load_calibration()
        self._configure()

    def _read_byte(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _read_u16(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        return data[0] | (data[1] << 8)

    def _read_s16(self, reg):
        v = self._read_u16(reg)
        return v if v < 32768 else v - 65536

    def _load_calibration(self):
        self.dig_T1 = self._read_u16(0x88)
        self.dig_T2 = self._read_s16(0x8A)
        self.dig_T3 = self._read_s16(0x8C)
        self.dig_P1 = self._read_u16(0x8E)
        self.dig_P2 = self._read_s16(0x90)
        self.dig_P3 = self._read_s16(0x92)
        self.dig_P4 = self._read_s16(0x94)
        self.dig_P5 = self._read_s16(0x96)
        self.dig_P6 = self._read_s16(0x98)
        self.dig_P7 = self._read_s16(0x9A)
        self.dig_P8 = self._read_s16(0x9C)
        self.dig_P9 = self._read_s16(0x9E)
        self.dig_H1 = self._read_byte(0xA1)
        self.dig_H2 = self._read_s16(0xE1)
        self.dig_H3 = self._read_byte(0xE3)
        e4 = self._read_byte(0xE4)
        e5 = self._read_byte(0xE5)
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        if self.dig_H4 > 2047:
            self.dig_H4 -= 4096
        e6 = self._read_byte(0xE6)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        if self.dig_H5 > 2047:
            self.dig_H5 -= 4096
        self.dig_H6 = self._read_byte(0xE7)
        if self.dig_H6 > 127:
            self.dig_H6 -= 256

    def _configure(self):
        self.i2c.writeto_mem(self.addr, 0xF2, b'\x01')
        self.i2c.writeto_mem(self.addr, 0xF4, b'\x27')
        self.i2c.writeto_mem(self.addr, 0xF5, b'\x00')

    def read_raw(self):
        data = self.i2c.readfrom_mem(self.addr, 0xF7, 8)
        raw_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_h = (data[6] << 8) | data[7]
        return raw_t, raw_p, raw_h

    def compensate_temperature(self, adc_t):
        var1 = (adc_t / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((adc_t / 131072.0 - self.dig_T1 / 8192.0) ** 2) * self.dig_T3
        self.t_fine = var1 + var2
        return self.t_fine / 5120.0

    def compensate_pressure(self, adc_p):
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = (var2 / 4.0) + (self.dig_P4 * 65536.0)
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            return 0
        p = 1048576.0 - adc_p
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self.dig_P9 * p * p / 2147483648.0
        var2 = p * self.dig_P8 / 32768.0
        p = p + (var1 + var2 + self.dig_P7) / 16.0
        return p / 100.0

    def compensate_humidity(self, adc_h):
        var_H = (self.t_fine - 76800.0)
        var_H = (adc_h - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * var_H)) * (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * var_H * (1.0 + self.dig_H3 / 67108864.0 * var_H)))
        var_H = var_H * (1.0 - self.dig_H1 * var_H / 524288.0)
        if var_H > 100.0:
            var_H = 100.0
        elif var_H < 0.0:
            var_H = 0.0
        return var_H

    def read(self):
        raw_t, raw_p, raw_h = self.read_raw()
        t = self.compensate_temperature(raw_t)
        p = self.compensate_pressure(raw_p)
        h = self.compensate_humidity(raw_h)
        return round(t, 2), round(p, 2), round(h, 2)


class BME280Sensor(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'bme280', c.get('location', ''), topic=c.get('topic'))
        bus = c.get('i2c_bus', 0)
        sda = Pin(c.get('sda', 0))
        scl = Pin(c.get('scl', 1))
        freq = c.get('freq', 400000)
        addr = c.get('addr', 0x76)
        self.i2c = I2C(bus, sda=sda, scl=scl, freq=freq)
        devices = self.i2c.scan()
        if addr not in devices:
            log('BME280 warning: addr 0x' + '{:02x}'.format(addr) + ' not found in scan: ' + str(devices))
        self.sensor = _BME280(self.i2c, addr)

    def read(self):
        t, p, h = self.sensor.read()
        return [
            {'name': 'temperature', 'value': t, 'unit': 'C'},
            {'name': 'pressure', 'value': p, 'unit': 'hPa'},
            {'name': 'humidity', 'value': h, 'unit': '%'}
        ]

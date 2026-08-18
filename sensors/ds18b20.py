import time, onewire, ds18x20
from machine import Pin
from sensors.base import Sensor
from core.logging import log

class DS18B20(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'ds18b20', c.get('location', ''), '', 'onewire_rom', topic=c.get('topic'))
        self.pin = c['pin']
        self._converting = False
        self._convert_start = 0
        self._pending_roms = []
        self.init()

    def init(self):
        self.ow = onewire.OneWire(Pin(self.pin))
        self.ds = ds18x20.DS18X20(self.ow)
        self.roms = self.ds.scan()
        if not self.roms:
            log('DS18B20: no devices found on pin ' + str(self.pin))

    def rom(self, r):
        return ''.join('{:02x}'.format(x) for x in r) if r else ''

    def read(self):
        if not self._converting:
            self.roms = self.ds.scan()
            if not self.roms:
                return []
            try:
                self.ds.convert_temp()
                self._converting = True
                self._convert_start = time.ticks_ms()
                self._pending_roms = list(self.roms)
            except Exception as e:
                log('DS18B20 convert error: ' + str(e))
                self.init()
            return []

        if time.ticks_diff(time.ticks_ms(), self._convert_start) < 750:
            return []

        self._converting = False
        out = []
        for r in self._pending_roms:
            try:
                v = self.ds.read_temp(r)
                hid = self.rom(r)
            except Exception as e:
                v = None
                hid = ''
                log('DS18B20 read error for ' + self.rom(r) + ': ' + str(e))
            if v is not None:
                out.append({
                    'name': 'temperature',
                    'value': round(v, 2),
                    'unit': 'C',
                    'hardware_id': hid,
                    'hardware_id_type': 'onewire_rom' if hid else ''
                })
        self._pending_roms = []
        return out

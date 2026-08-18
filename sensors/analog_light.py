from machine import ADC, Pin
from sensors.base import Sensor

class AnalogLightSensor(Sensor):
    def __init__(self, c):
        super().__init__(c['id'], 'analog_light', c.get('location', ''), topic=c.get('topic'))
        self.adc = ADC(Pin(c['pin']))
        self.vref = c.get('vref', 3.3)
        self.attenuation = c.get('attenuation', 1.0)

    def read(self):
        raw = self.adc.read_u16()
        percent = (raw / 65535.0) * 100.0
        voltage = (raw / 65535.0) * self.vref * self.attenuation
        return [
            {'name': 'light_level', 'value': round(percent, 1), 'unit': '%'},
            {'name': 'light_voltage', 'value': round(voltage, 3), 'unit': 'V'}
        ]

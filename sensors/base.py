from config import device, app
import time

class Sensor:
    def __init__(self, sensor_id, sensor_type, location, hardware_id='', hardware_id_type='', topic=None):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.location = location
        self.hardware_id = hardware_id or ''
        self.hardware_id_type = hardware_id_type or ''
        self.topic = topic

    def read(self):
        raise NotImplementedError

    def build_payload(self, m):
        return {
            'device': {
                'id': device.DEVICE_ID,
                'name': device.DEVICE_NAME,
                'firmware': app.APP_VERSION
            },
            'location': device.LOCATION,
            'sensor': {
                'id': self.sensor_id,
                'type': self.sensor_type,
                'hardware_id': m.get('hardware_id', self.hardware_id),
                'hardware_id_type': m.get('hardware_id_type', self.hardware_id_type),
                'location': self.location
            },
            'measurement': {
                'timestamp': m.get('timestamp', self._now()),
                'name': m.get('name'),
                'value': m.get('value'),
                'unit': m.get('unit')
            }
        }

    def build_error_payload(self, e):
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'hardware_id': self.hardware_id,
            'hardware_id_type': self.hardware_id_type,
            'location': self.location,
            'error': e
        }

    def _now(self):
        try:
            t = time.localtime()
            return '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z'.format(t[0], t[1], t[2], t[3], t[4], t[5])
        except:
            return None

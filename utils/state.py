from config import device

state = {
    'device': {
        'id': device.DEVICE_ID,
        'name': device.DEVICE_NAME,
        'version': '',
        'ip': '0.0.0.0',
        'wifi_connected': False,
        'wifi_rssi': None,
        'mqtt_connected': False,
        'mqtt_failures': 0,
        'uptime_s': 0,
        'sensor_count': 0,
        'free_ram': 0,
        'cpu_temp': None,
        'last_sensor_read_ms': 0
    },
    'location': device.LOCATION,
    'measurements': [],
    'latest': {}
}

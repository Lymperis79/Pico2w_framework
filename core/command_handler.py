import time, machine, ujson as json
from core.logging import log

class CommandHandler:
    def __init__(self, watchdog, mqtt, config, wifi, sensors):
        self.watchdog = watchdog
        self.mqtt = mqtt
        self.config = config
        self.wifi = wifi
        self.sensors = sensors

    def on_message(self, topic, message):
        self.watchdog.feed()
        try:
            data = json.loads(message.decode() if isinstance(message, bytes) else message)
        except Exception as e:
            log('Invalid JSON command: ' + str(e))
            self.mqtt.publish_event('command_error', {'error': 'invalid_json', 'details': str(e)})
            return

        cmd = data.get('command')
        log('Received command: ' + str(cmd))

        try:
            if cmd == 'restart':
                self.mqtt.publish_event('rebooting', {'reason': 'remote_command'})
                time.sleep_ms(200)
                machine.reset()
            elif cmd == 'wifi_reconnect':
                self.wifi.reconnect()
            elif cmd == 'mqtt_reconnect':
                self.mqtt.disconnect()
                self.mqtt.connect(self.on_message)
            elif cmd == 'get_config':
                self.mqtt.publish_event('config', self.config.get())
            elif cmd == 'set_config':
                self.config.apply(data.get('config', {}))
                self.mqtt.publish_event('config_updated', self.config.get())
            elif cmd == 'get_state':
                from utils.state import state
                self.mqtt.publish_event('state', dict(state))
            elif cmd == 'sensor_read':
                results = []
                for sensor in self.sensors:
                    try:
                        for m in sensor.read():
                            if m is not None:
                                results.append(sensor.build_payload(m))
                    except Exception as e:
                        results.append(sensor.build_error_payload(str(e)))
                self.mqtt.publish_event('sensor_read', results)
            else:
                self.mqtt.publish_event('command_error', {'error': 'unknown_command', 'command': cmd})
        except Exception as e:
            log('Command handler error: ' + str(e))
            self.mqtt.publish_event('command_error', {'error': 'handler_exception', 'details': str(e)})

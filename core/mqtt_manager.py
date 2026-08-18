import time, machine, ujson as json
from umqtt.simple import MQTTClient
from config import mqtt, device, app
from core.logging import log

class MQTTManager:
    def __init__(self, watchdog=None):
        self.watchdog = watchdog
        self.client = None
        self.connected = False
        self.callback = None
        self.failure_count = 0
        self.last_success_ms = 0

    def is_connected(self):
        return self.connected

    def connect(self, callback=None):
        if callback:
            self.callback = callback
        for _ in range(app.MQTT_MAX_ATTEMPTS_PER_CYCLE):
            try:
                self.client = MQTTClient(
                    mqtt.CLIENT_ID,
                    mqtt.BROKER,
                    port=mqtt.PORT,
                    user=mqtt.USERNAME,
                    password=mqtt.PASSWORD,
                    keepalive=mqtt.KEEPALIVE
                )
                self.client.set_last_will(
                    mqtt.STATUS_TOPIC,
                    json.dumps({'device_id': device.DEVICE_ID, 'status': 'offline'}),
                    retain=True,
                    qos=0
                )
                self.client.set_callback(self._callback)
                self.client.connect()
                self.client.subscribe(mqtt.COMMAND_TOPIC)
                self.connected = True
                self.failure_count = 0
                self.last_success_ms = time.ticks_ms()
                self.publish_status('online')
                log('MQTT connected to ' + str(mqtt.BROKER))
                return True
            except Exception as e:
                log('MQTT connect error: ' + str(e))
                self.connected = False
                self.failure_count += 1
                time.sleep(app.MQTT_RETRY_DELAY_S)
        if self.failure_count >= app.MQTT_REBOOT_AFTER_FAILURES:
            log('MQTT failures exceeded limit, rebooting')
            machine.reset()
        return False

    def _callback(self, t, m):
        if self.watchdog:
            self.watchdog.feed()
        if self.callback:
            try:
                self.callback(t, m)
            except Exception as e:
                log('MQTT callback error: ' + str(e))

    def loop(self):
        if not self.connected:
            return False
        try:
            self.client.check_msg()
            self.last_success_ms = time.ticks_ms()
            return True
        except Exception as e:
            log('MQTT loop error: ' + str(e))
            self.connected = False
            self.failure_count += 1
            return False

    def health_check(self):
        if not self.connected:
            return False
        try:
            self.client.ping()
            self.last_success_ms = time.ticks_ms()
            return True
        except Exception as e:
            log('MQTT ping error: ' + str(e))
            self.connected = False
            self.failure_count += 1
            return False

    def disconnect(self):
        try:
            if self.client:
                self.client.disconnect()
        except:
            pass
        self.connected = False

    def publish(self, topic, payload, retain=False):
        if not self.connected:
            return False
        try:
            msg = json.dumps(payload)
            if len(msg) > app.MQTT_COMMAND_MAX_SIZE:
                log('Payload too large, dropping')
                return False
            self.client.publish(topic, msg, retain=retain, qos=0)
            self.last_success_ms = time.ticks_ms()
            return True
        except Exception as e:
            log('MQTT publish error: ' + str(e))
            self.connected = False
            self.failure_count += 1
            return False

    def publish_measurement(self, payload):
        return self.publish(mqtt.MEASUREMENT_TOPIC, payload)

    def publish_event(self, event, details=None):
        return self.publish(mqtt.EVENT_TOPIC, {
            'device_id': device.DEVICE_ID,
            'event': event,
            'details': details
        })

    def publish_status(self, status):
        return self.publish(mqtt.STATUS_TOPIC, {
            'device_id': device.DEVICE_ID,
            'status': status
        }, retain=(status == 'offline'))

    def publish_heartbeat(self, uptime, ip, rssi, free_ram=None, cpu_temp=None):
        payload = {
            'device_id': device.DEVICE_ID,
            'status': 'online',
            'firmware': app.APP_VERSION,
            'uptime_s': uptime,
            'ip': ip,
            'wifi_rssi': rssi,
            'mqtt_failures': self.failure_count,
            'free_ram': free_ram,
            'cpu_temp': cpu_temp
        }
        return self.publish(mqtt.STATUS_TOPIC, payload, retain=False)

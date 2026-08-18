import time, machine, gc
from collections import deque
from config import app, mqtt
from core.watchdog import Watchdog
from core.wifi_manager import WiFiManager
from core.mqtt_manager import MQTTManager
from core.web_server import WebServer
from core.command_handler import CommandHandler
from core.config_manager import ConfigManager
from core.logging import log
from core.ntp import sync_time
from core.led_indicator import LEDIndicator
from sensors.registry import create_sensors
from utils.state import state

watchdog = Watchdog(app.WATCHDOG_TIMEOUT_MS)
config = ConfigManager()
wifi = WiFiManager(watchdog)
mqtt_mgr = MQTTManager(watchdog)
sensors = create_sensors()
handler = CommandHandler(watchdog, mqtt_mgr, config, wifi, sensors)
web = WebServer(watchdog, config, mqtt_mgr, wifi, sensors)
led = LEDIndicator()

state['device']['version'] = app.APP_VERSION
state['device']['sensor_count'] = len(sensors)
state['measurements'] = deque((), 100)

try:
    sync_time(timeout=app.NTP_TIMEOUT_S)
except Exception as e:
    log('NTP sync failed: ' + str(e))

wifi.connect()
mqtt_mgr.connect(handler.on_message)

start = time.ticks_ms()
last_sensor = 0
last_hb = 0
last_health = 0
last_gc = 0
last_led_hb = 0

def get_cpu_temp():
    try:
        adc = machine.ADC(4)
        reading = adc.read_u16() * 3.3 / 65535
        return round(27 - (reading - 0.706) / 0.001721, 1)
    except:
        return None

def sensor_topic(sensor):
    if hasattr(sensor, 'topic') and sensor.topic:
        return sensor.topic
    return mqtt.MEASUREMENT_TOPIC + '/' + sensor.sensor_id

def safe_delay_ms(ms):
    chunk = 50
    elapsed = 0
    while elapsed < ms:
        watchdog.feed()
        time.sleep_ms(chunk if (ms - elapsed) >= chunk else (ms - elapsed))
        elapsed += chunk

def update_latest_reading(payload, topic):
    hid = payload['sensor'].get('hardware_id', '')
    key = payload['sensor']['id'] + ':' + payload['measurement']['name'] + ':' + hid
    payload['topic'] = topic
    state['latest'][key] = payload

def main_loop():
    global last_sensor, last_hb, last_health, last_gc, last_led_hb
    watchdog.feed()
    now = time.ticks_ms()

    if time.ticks_diff(now, last_led_hb) >= app.LED_HEARTBEAT_INTERVAL_MS:
        led.heartbeat()
        last_led_hb = now

    if not wifi.is_connected():
        mqtt_mgr.disconnect()
        wifi.connect()

    if wifi.is_connected() and not mqtt_mgr.is_connected():
        mqtt_mgr.connect(handler.on_message)

    if mqtt_mgr.is_connected():
        mqtt_mgr.loop()

    if time.ticks_diff(now, last_health) >= app.MQTT_HEALTH_INTERVAL_MS:
        mqtt_mgr.health_check()
        last_health = now

    # Drain up to 5 web connections per loop to handle browser bursts
    for _ in range(5):
        if not web.serve_once():
            break

    if time.ticks_diff(now, last_sensor) >= config.sensor_interval_ms():
        sensor_count = len(sensors)
        for idx, sensor in enumerate(sensors):
            try:
                measurements = sensor.read()
                for measurement in measurements:
                    if measurement is None:
                        continue
                    payload = sensor.build_payload(measurement)
                    topic = sensor_topic(sensor)
                    mqtt_mgr.publish(topic, payload)
                    state['measurements'].append(payload)
                    update_latest_reading(payload, topic)
                    led.blink()
            except Exception as exc:
                log('Sensor ' + str(sensor.sensor_id) + ' error: ' + str(exc))
                mqtt_mgr.publish_event('sensor_error', sensor.build_error_payload(str(exc)))

            if idx < sensor_count - 1 and app.SENSOR_SEND_DELAY_MS > 0:
                safe_delay_ms(app.SENSOR_SEND_DELAY_MS)

        state['device']['last_sensor_read_ms'] = now
        last_sensor = now

    if time.ticks_diff(now, last_hb) >= app.HEARTBEAT_INTERVAL_MS:
        uptime = time.ticks_diff(now, start) // 1000
        mqtt_mgr.publish_heartbeat(
            uptime,
            wifi.ip_address(),
            wifi.rssi(),
            gc.mem_free(),
            get_cpu_temp()
        )
        last_hb = now

    if time.ticks_diff(now, last_gc) >= 300000:
        gc.collect()
        last_gc = now

    state['device']['uptime_s'] = time.ticks_diff(now, start) // 1000
    state['device']['wifi_connected'] = wifi.is_connected()
    state['device']['ip'] = wifi.ip_address()
    state['device']['wifi_rssi'] = wifi.rssi()
    state['device']['mqtt_connected'] = mqtt_mgr.is_connected()
    state['device']['mqtt_failures'] = mqtt_mgr.failure_count
    state['device']['free_ram'] = gc.mem_free()

    time.sleep_ms(20)

while True:
    try:
        main_loop()
    except Exception as e:
        log('FATAL LOOP ERROR: ' + str(e))
        try:
            mqtt_mgr.publish_event('fatal_error', {'error': str(e)})
        except:
            pass
        time.sleep_ms(500)
        machine.reset()

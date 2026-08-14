import time
from config import app
from core.watchdog import Watchdog
from core.wifi_manager import WiFiManager
from core.mqtt_manager import MQTTManager
from core.web_server import WebServer
from core.command_handler import CommandHandler
from core.config_manager import ConfigManager
from core.logging import log
from sensors.registry import create_sensors
from utils.state import state

watchdog=Watchdog(app.WATCHDOG_TIMEOUT_MS)
config=ConfigManager(); wifi=WiFiManager(watchdog); mqtt=MQTTManager(watchdog)
sensors=create_sensors()
handler=CommandHandler(watchdog,mqtt,config,wifi,sensors)
web=WebServer(watchdog,config,mqtt,wifi,sensors)
state['device']['version']=app.APP_VERSION
state['device']['sensor_count']=len(sensors)
wifi.connect(); mqtt.connect(handler.on_message)
start=time.ticks_ms(); last_sensor=0; last_hb=0; last_health=0
while True:
    watchdog.feed(); now=time.ticks_ms()
    if not wifi.is_connected():
        mqtt.disconnect(); wifi.connect()
    if wifi.is_connected() and not mqtt.is_connected():
        mqtt.connect(handler.on_message)
    mqtt.loop()
    if time.ticks_diff(now,last_health)>=app.MQTT_HEALTH_INTERVAL_MS:
        mqtt.health_check(); last_health=now
    web.serve_once()
    if time.ticks_diff(now,last_sensor)>=config.sensor_interval_ms():
        for sensor in sensors:
            try:
                for measurement in sensor.read():
                    payload=sensor.build_payload(measurement)
                    mqtt.publish_measurement(payload)
                    state['measurements'].append(payload)
                    if len(state['measurements'])>100: state['measurements'].pop(0)
            except Exception as exc:
                log('Sensor {} error: {}'.format(sensor.sensor_id,exc))
                mqtt.publish_event('sensor_error',sensor.build_error_payload(str(exc)))
        last_sensor=now
    if time.ticks_diff(now,last_hb)>=app.HEARTBEAT_INTERVAL_MS:
        mqtt.publish_heartbeat(time.ticks_diff(now,start)//1000,wifi.ip_address(),wifi.rssi()); last_hb=now
    state['device']['uptime_s']=time.ticks_diff(now,start)//1000
    state['device']['wifi_connected']=wifi.is_connected(); state['device']['ip']=wifi.ip_address(); state['device']['wifi_rssi']=wifi.rssi()
    state['device']['mqtt_connected']=mqtt.is_connected(); state['device']['mqtt_failures']=mqtt.failure_count
    time.sleep_ms(20)

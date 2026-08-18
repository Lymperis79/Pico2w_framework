# Pico2W Framework v3.6.8

Raspberry Pi Pico 2 W modular MicroPython IoT framework with onboard LED blink, per-sensor MQTT topics, latest-readings web dashboard, web Reboot button, and expanded HTTP API.

## What's New in v3.6.8
- **Fixed "Internal Server Error" on web dashboard** — completely rewritten web server with defensive try/except around every rendering step; now shows the actual error message on the page instead of a blank failure; each sensor card renders independently so one bad sensor can't break the whole page

## What's New in v3.6.7
- **Fixed DS18B20 showing only one value on web dashboard** — the `latest` dict key now includes the OneWire ROM address (`hardware_id`), so each physical device on the bus gets its own card

## What's New in v3.6.6
- **Fixed SyntaxError in web_server.py** — completely rewritten with simpler exception handling; removed `errno` import that caused issues on some MicroPython builds; added missing `time` import

## What's New in v3.6.5
- **Fixed web server unreachable / connection refused** — increased socket backlog from 1 to 5; drain up to 5 connections per main loop; reduced client recv timeout to 0.5s; hardened accept() error handling for EAGAIN/EWOULDBLOCK

## What's New in v3.6.4
- **Fixed onboard LED on Pico 2 W** — uses `Pin("LED", Pin.OUT)` alias for CYW43439 wireless chip; falls back to GPIO 25 for original Pico

## What's New in v3.6.3
- **Fixed `unsupported format character` error** — replaced `%` string formatting with string concatenation in the web server; MicroPython's `%` operator doesn't reliably handle `%%` escapes in long templates

## What's New in v3.6.2
- **Fixed `extra keyword arguments given` error** — removed `indent=2` from `json.dumps()` calls; MicroPython's `ujson` does not support the `indent` parameter

## What's New in v3.6.1
- **Fixed `ETIMEDOUT` in web server** — client sockets now have a 1-second recv timeout, preventing hangs when browsers open idle connections

## What's New in v3.6
- **New API endpoints:**
  - `GET /api/health` — Quick health snapshot (uptime, RAM, CPU temp, connection status, last sensor read age)
  - `GET /api/network` — Full network info including WiFi scan results
- Dashboard now shows quick links to all API endpoints
- Improved dashboard styling with N/A handling for missing values

## Web API Endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /` | HTML dashboard with latest sensor readings and device status |
| `GET /api/state` | Full device state JSON (device info, location, measurements buffer, latest readings) |
| `GET /api/health` | Health snapshot: uptime, free RAM, CPU temp, WiFi/MQTT status, sensor count, last read age |
| `GET /api/network` | Network info: IP, netmask, gateway, DNS, MAC, channel, RSSI, and nearby WiFi scan |
| `GET /api/config` | Runtime configuration JSON |
| `GET /api/restart` | Reboots the device immediately |

## Onboard LED Behavior
| Pattern | Meaning |
|---------|---------|
| Short flash (~80 ms) | Data was just published to MQTT |
| Double blink every 3 s | Device is alive and running (heartbeat) |
| Solid on | Boot or error state |
| Off for long periods | Device may be stuck or crashed |

## Built-in Sensor Drivers

| Driver | Type | Interface | Measurements |
|--------|------|-----------|--------------|
| `dht11` / `dht22` | DHT temp/humidity | 1-Wire GPIO | temperature, humidity |
| `ds18b20` | OneWire temp | 1-Wire GPIO | temperature (multi-device, non-blocking) |
| `bme280` | Temp/humidity/pressure | I2C | temperature, pressure, humidity |
| `aht20` | Temp/humidity | I2C | temperature, humidity |
| `sr04m` | Ultrasonic distance | GPIO trigger/echo | distance |
| `motion` | PIR motion | Digital GPIO | motion (bool, on-change) |
| `analog_light` | LDR / photoresistor | ADC GPIO | light_level (%), light_voltage (V) |
| `bh1750` | Digital light | I2C | illuminance (lx) |

## Setup
1. Copy all files to the Pico 2 W filesystem.
2. Edit `config/wifi.py` with your SSID and password.
3. Edit `config/mqtt.py` with your broker details.
4. Edit `config/device.py` with your device identity.
5. Edit `config/sensors.py` to enable only the sensors you have wired.
6. Optionally set `ADMIN_TOKEN` in `config/web.py`.

## Sensor Configuration Examples

**DHT22:** `{'id':'env','driver':'dht22','pin':15,'location':'room'}`

**DS18B20:** `{'id':'water','driver':'ds18b20','pin':4,'location':'tank'}`

**BME280:** `{'id':'climate','driver':'bme280','i2c_bus':0,'sda':0,'scl':1,'location':'greenhouse'}`

**AHT20:** `{'id':'aht','driver':'aht20','i2c_bus':0,'sda':0,'scl':1,'location':'office'}`

**SR04M:** `{'id':'level','driver':'sr04m','trigger_pin':5,'echo_pin':6,'location':'tank'}`

**Motion (PIR):** `{'id':'pir','driver':'motion','pin':14,'location':'door'}`

**Analog Light (LDR):** `{'id':'light','driver':'analog_light','pin':26,'location':'garden'}`

**BH1750:** `{'id':'lux','driver':'bh1750','i2c_bus':0,'sda':0,'scl':1,'location':'greenhouse'}`

## Adding a New Sensor
1. Create a new file in `sensors/` inheriting from `sensors.base.Sensor`.
2. Implement `read()` returning a list of measurement dicts.
3. Register the driver in `sensors/registry.py`.
4. Add an entry to `config/sensors.py`.

## MQTT Commands
- `restart` — Reboot the device
- `wifi_reconnect` — Force WiFi reconnect
- `mqtt_reconnect` — Force MQTT reconnect
- `get_config` — Publish current runtime config
- `set_config` — Update runtime config (e.g., sensor interval)
- `get_state` — Publish full device state
- `sensor_read` — Force immediate sensor read and publish results

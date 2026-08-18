import socket, machine, ujson as json, time
from config import device, web, app
from utils.state import state
from core.logging import log

CSS = """body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:20px;background:#f5f5f5;color:#333}
.card{background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08)}
.card h2{margin:0 0 12px 0;font-size:1.3em;color:#2c3e50}
.card .meta{color:#888;font-size:0.85em;margin-bottom:8px}
.reading{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #eee}
.reading:last-child{border-bottom:none}
.reading .name{font-weight:500}
.reading .value{font-size:1.2em;font-weight:700;color:#27ae60}
.reading .value-err{color:#e74c3c}
.reading .unit{color:#888;font-size:0.9em;margin-left:4px}
.status-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.status-online{background:#27ae60}
.status-offline{background:#e74c3c}
pre{background:#f8f8f8;padding:12px;border-radius:6px;overflow-x:auto;font-size:0.85em}
h1{color:#2c3e50;margin-top:0;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.btn{display:inline-block;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:0.85em;font-weight:500;border:none;cursor:pointer}
.btn-danger{background:#e74c3c;color:#fff}
.btn-secondary{background:#95a5a6;color:#fff}
.nav-links{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.api-links{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.api-links a{font-size:0.8em;color:#3498db;text-decoration:none}
.error-box{background:#f8d7da;color:#721c24;padding:16px;border-radius:8px;border:1px solid #f5c6cb;margin-bottom:16px}"""

class WebServer:
    def __init__(self, watchdog, config, mqtt, wifi, sensors):
        self.watchdog = watchdog
        self.config = config
        self.mqtt = mqtt
        self.wifi = wifi
        self.sensors = sensors
        a = socket.getaddrinfo('0.0.0.0', web.WEB_PORT)[0][-1]
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(a)
        self.sock.listen(5)
        self.sock.settimeout(0.01)

    def _check_auth(self, request):
        if web.ADMIN_TOKEN and web.ADMIN_TOKEN.startswith('CHANGE_'):
            return True
        if web.ADMIN_TOKEN in request:
            return True
        return False

    def _esc(self, text):
        if text is None:
            return ''
        text = str(text)
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    def _build_readings(self):
        try:
            latest = state.get('latest', {})
            if not latest:
                return '<p style="color:#888">No readings yet.</p>'
            groups = {}
            for key, payload in latest.items():
                try:
                    sid = payload.get('sensor', {}).get('id', 'unknown')
                    if sid not in groups:
                        groups[sid] = {
                            'type': payload.get('sensor', {}).get('type', 'unknown'),
                            'location': payload.get('sensor', {}).get('location', ''),
                            'topic': payload.get('topic', ''),
                            'readings': []
                        }
                    groups[sid]['readings'].append(payload.get('measurement', {}))
                except Exception as e:
                    log('Web build_readings item error: ' + str(e))
                    continue
            parts = []
            for sid, g in sorted(groups.items()):
                try:
                    rows = []
                    for m in g['readings']:
                        try:
                            name = m.get('name', '?')
                            value = m.get('value')
                            unit = m.get('unit', '')
                            vc = 'value' if value is not None else 'value value-err'
                            vs = str(value) if value is not None else 'N/A'
                            rows.append('<div class="reading"><span class="name">' + self._esc(name) + '</span><span><span class="' + vc + '">' + self._esc(vs) + '</span><span class="unit">' + self._esc(unit) + '</span></span></div>')
                        except Exception as e:
                            rows.append('<div class="reading"><span class="name">error</span><span class="value-err">' + self._esc(str(e)) + '</span></div>')
                    parts.append('<div class="card"><h2>' + self._esc(sid) + ' <span style="font-size:0.7em;color:#888">(' + self._esc(g['type']) + ')</span></h2><div class="meta">Location: ' + self._esc(g['location']) + ' | Topic: ' + self._esc(g['topic']) + '</div>' + ''.join(rows) + '</div>')
                except Exception as e:
                    parts.append('<div class="card"><h2>' + self._esc(sid) + '</h2><div class="error-box">Render error: ' + self._esc(str(e)) + '</div></div>')
            return ''.join(parts) if parts else '<p style="color:#888">No readable sensor data.</p>'
        except Exception as e:
            log('Web build_readings error: ' + str(e))
            return '<div class="error-box">Error building readings: ' + self._esc(str(e)) + '</div>'

    def _build_page(self):
        try:
            dev = state.get('device', {})
            sd = '<span class="status-dot status-online"></span>' if dev.get('mqtt_connected') else '<span class="status-dot status-offline"></span>'
            st = 'Online' if dev.get('mqtt_connected') else 'Offline'
            meta = sd + st + ' | IP: ' + str(dev.get('ip', '?')) + ' | RSSI: ' + str(dev.get('wifi_rssi', '?')) + ' dBm | Uptime: ' + str(dev.get('uptime_s', 0)) + 's'
            rh = self._build_readings()
            dev_json = ''
            try:
                dev_json = json.dumps(dev)
            except Exception as e:
                dev_json = '{"error": "' + str(e) + '"}'
            b = '<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + self._esc(device.DEVICE_NAME) + '</title><style>' + CSS + '</style></head><body>'
            b += '<h1>' + self._esc(device.DEVICE_NAME) + ' <span class="nav-links"><a href="/" class="btn btn-secondary">Refresh</a><a href="/api/restart" class="btn btn-danger" onclick="return confirm('Reboot now?')">Reboot</a></span></h1>'
            b += '<div class="card"><h2>Device Status</h2><div class="meta">' + meta + '</div><pre>' + self._esc(dev_json) + '</pre>'
            b += '<div class="api-links"><a href="/api/state">/api/state</a> <a href="/api/health">/api/health</a> <a href="/api/network">/api/network</a> <a href="/api/config">/api/config</a></div></div>'
            b += '<div class="card"><h2>Latest Sensor Readings</h2>' + rh + '</div></body></html>'
            return b
        except Exception as e:
            log('Web build_page error: ' + str(e))
            return '<!DOCTYPE html><html><body><h1>Error</h1><pre>' + self._esc(str(e)) + '</pre></body></html>'

    def _send_json(self, c, data):
        try:
            body = json.dumps(data)
        except Exception as e:
            body = json.dumps({'error': str(e)})
        h = 'HTTP/1.1 200 OK
Content-Type: application/json
Connection: close
Content-Length: ' + str(len(body)) + '

'
        c.send(h.encode())
        c.send(body.encode())
        c.close()

    def _send_html(self, c, body, status='200 OK'):
        h = 'HTTP/1.1 ' + status + '
Content-Type: text/html
Connection: close
Content-Length: ' + str(len(body)) + '

'
        c.send(h.encode())
        c.send(body.encode())
        c.close()

    def serve_once(self):
        try:
            c, addr = self.sock.accept()
        except:
            return False
        try:
            c.settimeout(0.5)
            try:
                r = c.recv(4096).decode()
            except:
                c.close()
                return True
            parts = r.split()
            if len(parts) < 2:
                self._send_html(c, '<h1>Bad Request</h1>', '400 Bad Request')
                return True
            path = parts[1]
            if not self._check_auth(r):
                self._send_html(c, '<h1>Unauthorized</h1>', '401 Unauthorized')
                return True
            if path == '/api/state':
                self._send_json(c, dict(state))
                return True
            elif path == '/api/health':
                try:
                    dev = state.get('device', {})
                    now = time.ticks_ms()
                    lr = dev.get('last_sensor_read_ms', 0)
                    age = time.ticks_diff(now, lr) if lr else None
                    self._send_json(c, {
                        'uptime_s': dev.get('uptime_s'),
                        'free_ram': dev.get('free_ram'),
                        'cpu_temp': dev.get('cpu_temp'),
                        'wifi_connected': dev.get('wifi_connected'),
                        'mqtt_connected': dev.get('mqtt_connected'),
                        'mqtt_failures': dev.get('mqtt_failures'),
                        'sensor_count': dev.get('sensor_count'),
                        'watchdog_timeout_ms': app.WATCHDOG_TIMEOUT_MS,
                        'last_sensor_read_age_ms': age,
                        'firmware': dev.get('version'),
                        'device_id': dev.get('id')
                    })
                except Exception as e:
                    self._send_json(c, {'error': str(e)})
                return True
            elif path == '/api/network':
                try:
                    self._send_json(c, {
                        'connected': self.wifi.is_connected(),
                        'ssid': self.wifi.ssid(),
                        'ip': self.wifi.ip_address(),
                        'netmask': self.wifi.netmask(),
                        'gateway': self.wifi.gateway(),
                        'dns': self.wifi.dns(),
                        'mac': self.wifi.mac(),
                        'channel': self.wifi.channel(),
                        'rssi': self.wifi.rssi(),
                        'scan': self.wifi.scan()
                    })
                except Exception as e:
                    self._send_json(c, {'error': str(e)})
                return True
            elif path == '/api/config':
                try:
                    self._send_json(c, self.config.get())
                except Exception as e:
                    self._send_json(c, {'error': str(e)})
                return True
            elif path == '/api/restart':
                self._send_json(c, {'status': 'rebooting'})
                machine.reset()
                return True
            else:
                body = self._build_page()
                self._send_html(c, body)
                return True
        except Exception as e:
            log('Web server error: ' + str(e))
            try:
                body = '<h1>500 Internal Server Error</h1><pre>' + self._esc(str(e)) + '</pre>'
                self._send_html(c, body, '500 Internal Server Error')
            except:
                try:
                    c.close()
                except:
                    pass
            return True

import time, machine, network
from config import wifi, app
from core.logging import log

class WiFiManager:
    def __init__(self, watchdog=None):
        self.watchdog = watchdog
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self._ssid = wifi.SSID

    def is_connected(self):
        return self.wlan.isconnected()

    def connect(self):
        if self.is_connected():
            return True
        for attempt in range(app.WIFI_MAX_ATTEMPTS):
            try:
                self.wlan.disconnect()
            except:
                pass
            log('WiFi connecting... attempt ' + str(attempt + 1) + '/' + str(app.WIFI_MAX_ATTEMPTS))
            self.wlan.connect(wifi.SSID, wifi.PASSWORD)
            deadline = time.ticks_add(time.ticks_ms(), app.WIFI_CONNECT_TIMEOUT_S * 1000)
            while not self.is_connected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
                if self.watchdog:
                    self.watchdog.feed()
                time.sleep_ms(200)
            if self.is_connected():
                log('WiFi connected: ' + self.ip_address())
                return True
            delay_end = time.ticks_add(time.ticks_ms(), app.WIFI_RETRY_DELAY_S * 1000)
            while time.ticks_diff(delay_end, time.ticks_ms()) > 0:
                if self.watchdog:
                    self.watchdog.feed()
                time.sleep_ms(100)
        log('WiFi failed after ' + str(app.WIFI_MAX_ATTEMPTS) + ' attempts, rebooting')
        machine.reset()

    def reconnect(self):
        return self.connect()

    def ip_address(self):
        try:
            return self.wlan.ifconfig()[0]
        except:
            return '0.0.0.0'

    def netmask(self):
        try:
            return self.wlan.ifconfig()[1]
        except:
            return '0.0.0.0'

    def gateway(self):
        try:
            return self.wlan.ifconfig()[2]
        except:
            return '0.0.0.0'

    def dns(self):
        try:
            return self.wlan.ifconfig()[3]
        except:
            return '0.0.0.0'

    def rssi(self):
        try:
            return self.wlan.status('rssi')
        except:
            return None

    def ssid(self):
        try:
            return self.wlan.config('essid')
        except:
            return self._ssid

    def channel(self):
        try:
            return self.wlan.config('channel')
        except:
            return None

    def mac(self):
        try:
            return ':'.join('{:02x}'.format(b) for b in self.wlan.config('mac'))
        except:
            return None

    def scan(self):
        """Scan for nearby networks. Returns list of dicts."""
        try:
            results = []
            networks = self.wlan.scan()
            for net in networks:
                ssid = net[0].decode('utf-8', 'replace')
                bssid = ':'.join('{:02x}'.format(b) for b in net[1])
                channel = net[2]
                rssi = net[3]
                auth = net[4]
                hidden = net[5]
                auth_str = self._auth_mode(auth)
                results.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'channel': channel,
                    'rssi': rssi,
                    'auth': auth_str,
                    'hidden': bool(hidden)
                })
            return sorted(results, key=lambda x: x['rssi'], reverse=True)
        except Exception as e:
            log('WiFi scan error: ' + str(e))
            return []

    def _auth_mode(self, mode):
        modes = {
            0: 'OPEN',
            1: 'WEP',
            2: 'WPA-PSK',
            3: 'WPA2-PSK',
            4: 'WPA/WPA2-PSK',
            5: 'WPA3-PSK',
            6: 'WPA2/WPA3-PSK'
        }
        return modes.get(mode, 'UNKNOWN(' + str(mode) + ')')

import machine, ujson as json, os
from core.logging import log

def update(manifest_url, watchdog=None):
    raise NotImplementedError('Install the full OTA deployment module before enabling remote OTA.')

def mark_ota_pending():
    try:
        with open('/ota_state.json', 'w') as f:
            f.write(json.dumps({'pending': True, 'failed': False}))
    except Exception as e:
        log('OTA state write error: ' + str(e))

def clear_ota_pending():
    try:
        if 'ota_state.json' in os.listdir('/'):
            os.remove('/ota_state.json')
    except:
        pass

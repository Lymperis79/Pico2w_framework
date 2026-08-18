# OTA rollback boot hook
import machine, os, ujson as json

STATE_FILE = '/ota_state.json'

def check_ota_rollback():
    try:
        if STATE_FILE in os.listdir('/'):
            with open(STATE_FILE) as f:
                state = json.loads(f.read())
            if state.get('pending'):
                state['pending'] = False
                state['failed'] = True
                with open(STATE_FILE, 'w') as f:
                    f.write(json.dumps(state))
                print('[BOOT] OTA rollback: previous update failed')
    except Exception as e:
        print('[BOOT] OTA check error:', e)

check_ota_rollback()

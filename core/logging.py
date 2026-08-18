import time

def log(message):
    t = time.localtime()
    ts = '{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(t[0], t[1], t[2], t[3], t[4], t[5])
    print('[' + ts + '] [PICO] ' + str(message))

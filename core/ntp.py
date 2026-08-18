import socket, struct, time, machine
from core.logging import log

NTP_DELTA = 2208988800

def sync_time(host='pool.ntp.org', port=123, timeout=5):
    addr = socket.getaddrinfo(host, port)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    msg = b'\x1b' + 47 * b'\x00'
    s.sendto(msg, addr)
    data = s.recv(48)
    s.close()
    t = struct.unpack('!12I', data)[10]
    t -= NTP_DELTA
    tm = time.gmtime(t)
    rtc = machine.RTC()
    rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    log('NTP sync OK: ' + str(t))
    return t

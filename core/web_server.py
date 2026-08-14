import socket,machine,ujson as json
from config import device,web
from utils.state import state
class WebServer:
 def __init__(self,watchdog,config,mqtt,wifi,sensors):
  self.watchdog=watchdog; self.config=config; self.mqtt=mqtt; self.wifi=wifi
  a=socket.getaddrinfo('0.0.0.0',web.WEB_PORT)[0][-1]; self.sock=socket.socket(); self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); self.sock.bind(a); self.sock.listen(1); self.sock.settimeout(.01)
 def serve_once(self):
  try:c,_=self.sock.accept()
  except OSError:return
  try:
   r=c.recv(4096).decode(); path=r.split(' ')[1]
   if path=='/api/state': body=json.dumps(state); ct='application/json'
   else: body='<html><meta http-equiv="refresh" content="5"><h2>{}</h2><pre>{}</pre><table border=1><tr><th>Sensor</th><th>Type</th><th>Hardware ID</th><th>ID Type</th><th>Measurement</th><th>Value</th></tr>{}</table></html>'.format(device.DEVICE_NAME,json.dumps(state['device']),''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(x['sensor']['id'],x['sensor']['type'],x['sensor']['hardware_id'],x['sensor']['hardware_id_type'],x['measurement']['name'],x['measurement']['value']) for x in state['measurements'])); ct='text/html'
   h='HTTP/1.1 200 OK\r\nContent-Type: {}\r\nConnection: close\r\nContent-Length: {}\r\n\r\n'.format(ct,len(body)); c.send(h); c.send(body)
  except: pass
  finally:
   try:c.close()
   except:pass

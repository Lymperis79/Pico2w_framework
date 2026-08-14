import machine,ujson as json
class CommandHandler:
 def __init__(self,watchdog,mqtt,config,wifi,sensors): self.watchdog=watchdog; self.mqtt=mqtt; self.config=config; self.wifi=wifi; self.sensors=sensors
 def on_message(self,topic,message):
  self.watchdog.feed(); data=json.loads(message.decode() if isinstance(message,bytes) else message); cmd=data.get('command')
  if cmd=='restart': machine.reset()
  elif cmd=='wifi_reconnect': self.wifi.reconnect()
  elif cmd=='mqtt_reconnect': self.mqtt.disconnect(); self.mqtt.connect(self.on_message)
  elif cmd=='get_config': self.mqtt.publish_event('config',self.config.get())
  elif cmd=='set_config': self.config.apply(data.get('config',{}))

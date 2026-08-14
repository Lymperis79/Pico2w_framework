from config import device,app
class Sensor:
 def __init__(self,sensor_id,sensor_type,location,hardware_id='',hardware_id_type=''): self.sensor_id=sensor_id; self.sensor_type=sensor_type; self.location=location; self.hardware_id=hardware_id or ''; self.hardware_id_type=hardware_id_type or ''
 def read(self): raise NotImplementedError
 def build_payload(self,m): return {'device':{'id':device.DEVICE_ID,'name':device.DEVICE_NAME,'firmware':app.APP_VERSION},'location':device.LOCATION,'sensor':{'id':self.sensor_id,'type':self.sensor_type,'hardware_id':m.get('hardware_id',self.hardware_id),'hardware_id_type':m.get('hardware_id_type',self.hardware_id_type),'location':self.location},'measurement':{'timestamp':m.get('timestamp'),'name':m.get('name'),'value':m.get('value'),'unit':m.get('unit')}}
 def build_error_payload(self,e): return {'sensor_id':self.sensor_id,'sensor_type':self.sensor_type,'hardware_id':self.hardware_id,'hardware_id_type':self.hardware_id_type,'location':self.location,'error':e}

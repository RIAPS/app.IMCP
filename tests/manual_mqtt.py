import json
import logging
import riaps.interfaces.mqtt.MQTT as MQTT

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

path_to_config = "/home/riaps/projects/RIAPS/app.MgManage_refactor/cfg_vanderbilt/mqtt.yaml"
cfg = MQTT.load_mqtt_config(path_to_config=path_to_config)

thread = MQTT.MQThread(logger, cfg)
thread.mqtt_client()
thread.mqtt_connect()

payload = {"SecCtrlEnable": 1}
topic = "mg/event"
data = json.dumps(payload)
MQTTMessageInfo = thread.send(topic=topic, data=data, qos=0)

import json

from riaps.interfaces.mqtt.MqttDevice import MqttDevice

from applibs.log_preprocessor import log_json


class MQTT(MqttDevice):
    def __init__(self, config):
        super().__init__(config)
        self.logger.debug("Init mqtt device")

        # mapping from uuid in code to gui id
        self.mapping = self.mqtt_config["riaps_to_mqtt_mapping"]
        self.mqtt2riaps = dict()
        for key, value in self.mapping.items():
              self.mqtt2riaps[value] = key         

    def on_mqtt_sub(self):
        msg = self.mqtt_sub.recv_pyobj()
        self.logger.debug("MQTT: on_mqtt_sub"
                          f"msg: {msg}")

        self.sending_mqtt_message(msg)

    def on_trigger(self):
        msg = self.trigger.recv_pyobj()  # Receive message from mqtt broker
        self.logger.info('on_trigger():%r' % msg)
        log_json(self.logger, "info", "on_trigger()", event="RECEIVED MESSAGE FROM MQTT BROKER")
        # TODO: Should this conversion go in the SYSTEM_OPERARTOR instead?
        #  basically I don't like having multiple checks against the event key, but if I move it I have to load the mapping from the config file. 
        if "relay_click" == msg.get("event", None):
            riaps_uid = self.mqtt2riaps[msg.get("requestedRelay")]
            msg["requestedRelay"] = riaps_uid

        self.gui_pub.send_pyobj(msg)  # forward message from GUI to the components

    def sending_mqtt_message(self, msg):
        # send out the message directly for data
        temp_topic = "riaps/data/" + msg['sender']
        data_msg = {"data": json.dumps(msg),
                    "topic": temp_topic}
        self.send_mqtt(data_msg)

        # prepare the message for SVG
        uuid = msg.get("sender")
        diagram_id = self.mapping[uuid]  # This is the element id used on the SVG file.
        schema_name = msg.get("schema_name")
        payload = None
        if schema_name == "DgGeneralMsg":
            #  Handle data from generator
            payload = {
                "command": "update_text",
                "selector": f"#{diagram_id}_text",
                "text": f"P: {round(msg.get('activePower'), 4)}"
            }
        elif schema_name == "RelayMsg":
            #  Handle data from relay
            connected = msg.get("connected")
            fill = "red" if connected else "green"
            payload = [
                {
                    "command": "update_style",
                    "selector": f"#{diagram_id}",
                    "style": {"fill": fill}
                },
                {
                    "command": "update_text",
                    "selector": f"#{diagram_id}_text",
                    "text": f"P: {round(msg.get('activePower'), 4)}"
                }
            ]
        if payload:
            msg = {"data": json.dumps(payload),
                   "topic": "riaps/ctrl"}
            self.send_mqtt(msg)

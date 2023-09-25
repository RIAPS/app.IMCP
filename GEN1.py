# riaps:keep_import:begin
import capnp
import datetime

import riaps.interfaces.modbus.device_capnp as msg_struct
from riaps.interfaces.modbus.ModbusDeviceComponent import ModbusDeviceComponent
# riaps:keep_import:end


class GEN1(ModbusDeviceComponent):

    # riaps:keep_constr:begin
    def __init__(self, path_to_device_list):
        super().__init__(path_to_device_list)
    # riaps:keep_constr:end

    # riaps:keep_device_port:begin
    def on_device_port(self):
        # receive from riaps and send to modbus device thread
        start = datetime.datetime.now()  # measure how long it takes to complete query
        msg_bytes = self.device_port.recv()  # required to remove message from queue
        riaps_msg = msg_struct.DeviceQry.from_bytes(msg_bytes).to_dict()

        modbus_msg = {"to_device": riaps_msg["device"],
                      "parameters": riaps_msg["params"],
                      "operation": riaps_msg["operation"],
                      "values": riaps_msg["values"],
                      "msgcounter": riaps_msg["msgcounter"]}

        self.logger.info(f"GEN1 | on_device_port | modbus_msg: {modbus_msg}")

        self.send_modbus(modbus_msg)
    # riaps:keep_device_port:end

    # riaps:keep_poller:begin
    def on_poller(self):
        now = self.poller.recv_pyobj()
    # riaps:keep_poller:end

    # riaps:keep_modbus_cmd_port:begin
    def on_modbus_command_port(self):
        # Receive response from modbus device
        msg = super().on_modbus_command_port()
        self.logger.info(f"GEN1 | on_modbus_command_port | msg: {msg}")

        ans_msg = msg_struct.DeviceAns.new_message()
        ans_msg.returnStatus = msg["return_status"]
        ans_msg.device = msg["device_name"]
        ans_msg.operation = msg["operation"]
        ans_msg.params = msg["parameters"]
        ans_msg.values = msg["values"]
        ans_msg.msgcounter = msg["msgcounter"]

        msgbytes = ans_msg.to_bytes()
        self.device_port.send(msgbytes)

        if self.global_debug_mode == 1:
            log_str = f"ModbusDevice::on_modbus_cmd_port( {ans_msg.device}:ANSWER:{ans_msg.params}:{ans_msg.values}:{ans_msg.msgcounter} )"
            self.logger.info(log_str)
    # riaps:keep_modbus_cmd_port:end

    # riaps:keep_modbus_evt_port:begin
    def on_modbus_event_port(self):
        msg = super().on_modbus_event_port()
        evtmsg = msg_struct.DeviceEvent.new_message()
        evtmsg.event = msg.event
        evtmsg.command = msg.command
        evtmsg.names = list(msg.names)
        evtmsg.values = list(msg.values)
        evtmsg.units = list(msg.units)
        evtmsg.device = msg.device
        evtmsg.error = msg.error
        evtmsg.et = msg.et
        self.post_event(evtmsg)
        if self.global_debug_mode == 1:
            log_str = f"ModbusDevice::on_modbus_evt_port( {evtmsg.device}:{evtmsg.event}:{evtmsg.names}:{evtmsg.values} )"
            self.logger.info(log_str)
    # riaps:keep_modbus_evt_port:end

    # riaps:keep_impl:begin
    # post an event if the required attributes exist and the event is valid
    def post_event(self, evt):
        if evt is None:
            self.logger.warning("Invalid event: None")
            return

        if not hasattr(self, "event_port"):
            self.logger.warning(f"Modbus attribute [self.event_port] is not defined! Cannot process event {evt}!")
            return

        self.event_port.send(evt.to_bytes())
        if self.global_debug_mode == 1:
            log_str = f"ModbusDevice::postEvent({evt.device}, {evt.event}, {evt.names}, {evt.values})"
            self.logger.info(log_str)
    # riaps:keep_impl:end

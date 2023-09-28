# riaps:keep_import:begin
import time
from riaps.run.comp import Component
import capnp
import imcp_capnp
import applibs.helper as helper
from applibs.log_preprocessor import log_json

# riaps:keep_import:end

debugMode = helper.debugMode


# riaps:keep_constr:begin
class SYSTEM_OPERATOR_SINGLE_FEEDER(Component):
    def __init__(self, mqtt_subsample_rate):
        super().__init__()
        self.relayStatus = {}  # set by messages from relays
        self.target_status_of_relays = {}  # set from GUI
        self.requested_relay = "NONE"  # This means we can only control 1 at a time. And that is what we want.

        #  the control_values come from the GUI
        self.control_values = {"StartStop": 0,
                               "GridTiedOp": 0,
                               "SecCtrlEnable": 0,
                               "SecCtrlAngleEnable": 0,
                               "RegulationSignal": 0,
                               # If we are providing power control this is P/Q,
                               # if we are providing frequency and voltage support for the grid this is F/V.
                               # In that case we need calculate the P/Q from the F/V.
                               "RegulationSignal2": 0}
        self.mqtt_subsample_rate = mqtt_subsample_rate
        self.mqtt_peer_msg_counter = {}

        self.operator_msgs_sent = 0
        self.node_states = {}  # records the current FSM state off all components that publish state.

        self.appInitReady = False

    # riaps:keep_constr:end

    # riaps:keep_poller:begin
    def on_poller(self):
        now = self.poller.recv_pyobj()
        if not self.appInitReady:
            self.appInitReady = True
            log_json(self.logger, "info",
                     message=f"{self.getName()} component Initialized.",
                     event="COMPONENT_INITIALIZED")
            self.poller.halt()

    # riaps:keep_poller:end

    # riaps:keep_state_sub:begin
    def on_state_sub(self):
        msg_bytes = self.state_sub.recv()
        msg = imcp_capnp.StateMsg.from_bytes(msg_bytes)
        if debugMode:
            self.logger.info(f"{helper.Yellow}"
                             f"Operator\n"
                             f"on_state_sub:{msg.sender} \n"
                             f"recv state sub msgcounter: {msg.msgcounter} \n"
                             f"state: {msg.currentState} \n"
                             f" breaker: {msg.breaker} and action: {msg.action} \n"
                             f" group: {msg.group}  and reconfigcontrol {msg.reconfigcontrol}\n"
                             f"{helper.RESET}")

        self.node_states[msg.sender] = msg.currentState
    # riaps:keep_state_sub:end

    # riaps:keep_consensus_sub:begin
    def on_consensus_sub(self):
        msg_bytes = self.consensus_sub.recv()
        msg = imcp_capnp.DgGeneralMsg.from_bytes(msg_bytes).to_dict()

        if debugMode:
            self.logger.info(f"{helper.BrightCyan}"
                             f"System Operator.py - on_consensus_sub \n"
                             f"consensus msg: {msg}"
                             f"{helper.RESET}")

        self.subsample_and_publish_mqtt_message(msg, "DgGeneralMsg")

    # riaps:keep_consensus_sub:end

    # riaps:keep_relay_sub:begin
    def on_relay_sub(self):
        msg_bytes = self.relay_sub.recv()
        msg_capnp = imcp_capnp.RelayMsg.from_bytes(msg_bytes)
        relayID = msg_capnp.sender
        msg = msg_capnp.to_dict()
        self.relayStatus[relayID] = {"connected": msg["connected"]}
        self.subsample_and_publish_mqtt_message(msg, "RelayMsg")

        self.send_operator_msg(self.requested_relay)

        if debugMode:
            self.logger.info(f"{helper.BrightMagenta}\n"
                             f"System Operator.py - on_relay_sub \n"
                             f"msg: {msg_capnp}"
                             f"{helper.RESET}")
    # riaps:keep_relay_sub:end

    # riaps:keep_gui_sub:begin
    def on_gui_sub(self):
        msg = self.gui_sub.recv_pyobj()
        self.logger.info(f"{helper.BrightBlue}\n"
                         f"System Operator.py - on_gui_sub\n"
                         f"msg {msg}")

        if msg.get("event") == "relay_click":
            self.requested_relay = msg.get("requestedRelay")
            requested_action = msg.get("requestedAction")
            self.target_status_of_relays[self.requested_relay] = requested_action
        if "StartStop" in msg:
            self.control_values["StartStop"] = msg["StartStop"]
        if "SecCtrlEnable" in msg:
            self.control_values["SecCtrlEnable"] = msg["SecCtrlEnable"]
        if "active" in msg:
            self.control_values["RegulationSignal"] = msg["active"]
            self.control_values["RegulationSignal2"] = msg["reactive"]
        
        self.logger.info(f"{helper.BrightBlue}\n"
                             f"System Operator.py - on_gui_sub\n"
                             f"self.control_values {self.control_values}")

        self.send_operator_msg(self.requested_relay)
    # riaps:keep_gui_sub:end

    # riaps:keep_impl:begin

    def subsample_and_publish_mqtt_message(self, msg, schema_name):
        """
        This function publishes messages to a mqtt broker.
        It allows the user to specify a subsample rate and only sends every nth message from a peer on a given topic.
        """
        sender = msg["sender"]
        if sender not in self.mqtt_peer_msg_counter:
            self.mqtt_peer_msg_counter[sender] = {}
        if schema_name not in self.mqtt_peer_msg_counter[sender]:
            self.mqtt_peer_msg_counter[sender][schema_name] = 0

        self.mqtt_peer_msg_counter[sender][schema_name] += 1

        if self.mqtt_peer_msg_counter[sender][schema_name] >= self.mqtt_subsample_rate:
            self.mqtt_peer_msg_counter[sender][schema_name] = 0
            msg["schema_name"] = schema_name
            self.mqtt_pub.send_pyobj(msg)

    def filter_mqtt(self, msg, schema_name):
        """
        This function publishes messages to a mqtt broker.
        It allows the user to specify a subsample rate and only send every nth messages from a given peer.
        """
        sender = msg["sender"]
        self.mqtt_peer_msg_count[sender] = self.mqtt_peer_msg_count.get(sender, 0) + 1
        if self.mqtt_peer_msg_count[sender] % self.mqtt_peer_msg_count["subsample_nth"] != 0:
            return

        self.mqtt_peer_msg_count[sender] = 0
        msg["schema_name"] = schema_name
        self.mqtt_pub.send_pyobj(msg)

    def send_operator_msg(self, requested_relay):
        operator_msg = imcp_capnp.OperatorMsg.new_message()
        operator_msg.sender = 'OPAL'  # self.dvc["uuid"]
        operator_msg.type = 'regD'
        # operator_msg.type is not used, but could be used to distinguish if we are using P/Q or F/V control.
        # regD stands for regulation dynamic which is fast and means the regulation signal is F/V.
        # power stands for power control and means the regulation signal is P/Q.

        self.operator_msgs_sent += 1
        operator_msg.msgcounter = self.operator_msgs_sent
        operator_msg.opalParams = list(self.control_values.keys())
        operator_msg.opalValues = list(self.control_values.values())
        operator_msg.requestedRelay = requested_relay
        operator_msg.requestedAction = self.target_status_of_relays.get(requested_relay, "NONE")
        operator_msg.timestamp = time.time()
        operator_msg_bytes = operator_msg.to_bytes()

        if debugMode:
            self.logger.info(f"{helper.Cyan}\n"
                             f"OPAL_CTRL_MANAGER.py "
                             f"send_operator_msg \n"
                             f"msg: {operator_msg}"
                             f"{helper.RESET}")

        self.operator_pub.send(operator_msg_bytes)
    # riaps:keep_impl:end

# riaps:keep_import:begin
from riaps.run.comp import Component
import applibs.helper as helper
import spdlog
import capnp
import riaps_capnp
import modbuslibs.device_capnp as msgstruct
import time
import os
from RELAYF1_MANAGER import relay_status_sync
from RELAYF1_MANAGER import relay_msg_to_msgdict

# riaps:keep_import:end

debugMode = helper.debugMode
msgcounterLimit = helper.msgcounterLimit


# riaps:keep_constr:begin
class SYSTEM_OPERATOR(Component):
    def __init__(self):
        super().__init__()
        self.pid = os.getpid()
        self.init = False
        self.appInitCounter = 0
        self.appInitReady = False
        self.display_counter_Q = 0

        # parameters for opal control
        self.CtrlParameters = []
        self.CtrlValues = []
        self.msgcounter = 0
        self.startStop_opal = 0
        self.gridBreaker_opal = 1
        self.secondaryCtrl_opal = 0
        self.secondaryAngleCtrl_opal = 0
        self.regulationSignal = 0
        self.regulationSignal2 = 0

        # parameters for reconfiguration
        self.requestedRelay = 'NONE'
        self.requestedAction = 'NONE'
        self.relayMessages = {}
        self.relayStatus = {}

        # counter for mqtt message, sending every 1 second
        self.mqtt_counters = {}
        # counter for testing
        self.testCounter20second = 0
        self.testCounter20second_enable = 0
        self.currentTestState = 'RESET'
        self.nextTestState = 'RESET'

    # riaps:keep_constr:end

    # riaps:keep_local_event_port:begin
    def on_local_event_port(self):
        evt_bytes = self.local_event_port.recv()
        evt = msgstruct.DeviceEvent.from_bytes(evt_bytes)
        self.logger.info('received event from opal: %s' % str(evt))

    # riaps:keep_local_event_port:end

    def on_init_clock(self):
        now = self.init_clock.recv_pyobj()
        self.appInitReady = False
        self.poller.halt()
        self.logger.info(f"app initializing, init_clock running and poller halt()")

        if self.appInitCounter == 5:
            self.appInitReady = True
            self.poller.launch()
            self.init_clock.halt()
            self.logger.info(f"app starting, init_clock halt and poller launched")

        self.appInitCounter = self.appInitCounter + 1

    # riaps:keep_poller:begin
    def on_poller(self):
        on_clock_start = time.time()
        now = self.poller.recv_pyobj()
        if debugMode:
            self.logger.info(f"on_poller()[{str(self.pid)}]: {str(now)}")

        self.ReconfigurationManager()

        if self.appInitReady:
            msg = msgstruct.DeviceQry.new_message()
            msg.device = 'OPAL'  # self.device_name
            msg.operation = "READ"
            msg.params = ["StartStop", "GridTiedOp", "SecCtrlEnable", "SecCtrlAngleEnable", "RegulationSignal",
                          "RegulationSignal2"]
            msg.values = [-1] * len(msg.params)
            msg.timestamp = time.time()
            self.msgcounter += 1
            msg.msgcounter = self.msgcounter
            msg_bytes = msg.to_bytes()

            if debugMode:
                self.logger.info(f"{helper.Cyan}"
                                 f"OPAL_CTRL_MANAGER.py "
                                 f"on_poller \n"
                                 f"send qry msgcounter {self.msgcounter} \n"
                                 f"msg.operation: {msg}"
                                 f"{helper.reset}")

            self.device_port.send(msg_bytes)
        else:
            pass

    # riaps:keep_poller:end

    # riaps:keep_device_port:begin
    def on_device_port(self):
        msg_bytes = self.device_port.recv()
        msg = msgstruct.DeviceAns.from_bytes(msg_bytes)

        self.startStop_opal, self.gridBreaker_opal, self.secondaryCtrl_opal, \
        self.secondaryAngleCtrl_opal, self.regulationSignal, self.regulationSignal2 = msg.values

        if debugMode:
            self.logger.info('received commands from opal: %s' % str(msg))

        operator_msg = riaps_capnp.OperatorMsg.new_message()
        operator_msg.sender = 'OPAL'  # self.dvc["uuid"]
        operator_msg.type = 'regD'
        operator_msg.msgcounter = msg.msgcounter
        operator_msg.opalParams = ["StartStop", "GridTiedOp", "SecCtrlEnable", "SecCtrlAngleEnable", "RegulationSignal",
                                   "RegulationSignal2"]
        operator_msg.opalValues = [self.startStop_opal, self.gridBreaker_opal, self.secondaryCtrl_opal,
                                   self.secondaryAngleCtrl_opal, self.regulationSignal, self.regulationSignal2]
        operator_msg.requestedRelay = self.requestedRelay
        operator_msg.requestedAction = self.requestedAction
        operator_msg.timestamp = time.time()
        operator_msg_bytes = operator_msg.to_bytes()

        if debugMode:
            self.logger.info(f"{helper.BrightMagenta}"
                             f"OPAL_CTRL_MANAGER.py "
                             f"on_device_port "
                             f"pub opal control msgcounter: {msg.msgcounter}"
                             f"{helper.reset}")

        self.operator_pub.send(operator_msg_bytes)

    # riaps:keep_device_port:end

    # riaps:keep_gui_sub:begin
    def on_gui_sub(self):
        command = self.gui_sub.recv()

    # riaps:keep_gui_sub:end

    # riaps:keep_consensus_sub:begin
    def on_consensus_sub(self):
        msg_bytes = self.consensus_sub.recv()
        capnp_msg = riaps_capnp.DgGeneralMsg.from_bytes(msg_bytes)
        self.logger.debug("System operator: on_consensus_sub"
                          f"msg: {capnp_msg}")

        # send DER message to mqtt
        msg = capnp_msg.to_dict()
        if msg['sender'] in self.mqtt_counters:
            self.mqtt_counters[msg['sender']] = self.mqtt_counters[msg['sender']] + 1
        else:
            self.mqtt_counters[msg['sender']] = 0

        # sending out messages every 1 second
        if self.mqtt_counters[msg['sender']] >= 5:
            del self.mqtt_counters[msg['sender']]
            msg["schema_name"] = "DgGeneralMsg"
            self.mqtt_pub.send_pyobj(msg)

    # riaps:keep_consensus_sub:end

    # riaps:keep_relay_sub:begin
    def on_relay_sub(self):
        msg_bytes = self.relay_sub.recv()
        capnp_msg = riaps_capnp.RelayMsg.from_bytes(msg_bytes)
        self.logger.debug("System operator: on_relay_sub"
                          f"msg: {capnp_msg}")

        relayID = capnp_msg.sender
        self.relayMessages[relayID] = relay_msg_to_msgdict(capnp_msg)
        self.relayStatus[relayID] = relay_status_sync(self.relayMessages[relayID])

        # send relay message to mqtt
        msg = capnp_msg.to_dict()
        if msg['sender'] in self.mqtt_counters:
            self.mqtt_counters[msg['sender']] = self.mqtt_counters[msg['sender']] + 1
        else:
            self.mqtt_counters[msg['sender']] = 0

        # sending out messages every 1 second
        if self.mqtt_counters[msg['sender']] >= 5:
            del self.mqtt_counters[msg['sender']]
            msg["schema_name"] = "RelayMsg"
            self.mqtt_pub.send_pyobj(msg)

        if debugMode:
            self.logger.info(f"{helper.BrightMagenta}"
                             f"on_relay_sub:{msg.sender}, status: {msg.connected} \n"
                             f"recv relay sub msgcounter: {msg.msgcounter} \n"
                             f"p: {msg.activePower} and q: {msg.reactivePower} \n"
                             f"f diff: {msg.freqSlip} and V diff: {msg.voltDiff} and A diff:{msg.angDiff} \n"
                             f"{helper.reset}")
        # riaps:keep_relay_sub:end

    def ReconfigurationManager(self):

        self.requestedRelay = 'NONE'
        self.requestedAction = 'NONE'

        if self.testCounter20second_enable:
            self.testCounter20second += 1
        else:
            self.testCounter20second = 0

        if self.testCounter20second >= 101:
            self.testCounter20second = 0

        # state Machine for testing
        if self.currentTestState == 'RESET':
            self.nextTestState = self.currentTestState
            if self.secondaryCtrl_opal >= 1:
                self.nextTestState = 'GRID_POI_POWER_CONTROL'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'GRID_POI_POWER_CONTROL':
            self.nextTestState = self.currentTestState
            self.testCounter20second_enable = True
            if self.testCounter20second >= 100:
                self.nextTestState = 'PLANNED_ISLANDING'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'PLANNED_ISLANDING':
            self.nextTestState = self.currentTestState
            self.testCounter20second_enable = True
            self.requestedRelay = 'PCC'
            self.requestedAction = 'OPEN'
            if (self.testCounter20second >= 100 and
                    self.relayStatus['F1PCC']['status'] == 'disconnected' and
                    self.relayStatus['F2PCC']['status'] == 'disconnected' and
                    self.relayStatus['F3PCC']['status'] == 'disconnected'):
                self.nextTestState = 'ISLANDED'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'ISLANDED':
            self.testCounter20second_enable = True
            if self.testCounter20second >= 100:
                self.nextTestState = 'CONNECT12'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'CONNECT12':
            self.testCounter20second_enable = True
            self.requestedRelay = 'F1108'
            self.requestedAction = 'CLOSE'
            if (self.testCounter20second >= 100 and
                    self.relayStatus['F1108']['status'] == 'connected'):
                self.nextTestState = 'ISLANDED12'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'ISLANDED12':
            self.testCounter20second_enable = True
            if self.testCounter20second >= 50:  # short the duration for this state
                self.nextTestState = 'CONNECT23'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'CONNECT23':
            self.testCounter20second_enable = True
            self.requestedRelay = 'F2217'
            self.requestedAction = 'CLOSE'
            if (self.testCounter20second >= 100 and
                    self.relayStatus['F2217']['status'] == 'connected'):
                self.nextTestState = 'ISLANDED123'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'ISLANDED123':
            self.testCounter20second_enable = True
            if self.testCounter20second >= 100:
                self.nextTestState = 'DISCONNECT23'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'DISCONNECT23':
            self.testCounter20second_enable = True
            self.requestedRelay = 'F2217'
            self.requestedAction = 'OPEN'
            if (self.testCounter20second >= 100 and
                    self.relayStatus['F2217']['status'] == 'disconnected'):
                self.nextTestState = 'ISLANDED12_B'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'ISLANDED12_B':
            self.testCounter20second_enable = True
            if self.testCounter20second >= 50:  # short the duration for this state
                self.nextTestState = 'DISCONNECT12'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'DISCONNECT12':
            self.testCounter20second_enable = True
            self.requestedRelay = 'F1108'
            self.requestedAction = 'OPEN'
            if (self.testCounter20second >= 100 and
                    self.relayStatus['F1108']['status'] == 'disconnected'):
                self.nextTestState = 'ISLANDED_B'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'ISLANDED_B':
            self.testCounter20second_enable = True
            if self.testCounter20second >= 100:
                self.nextTestState = 'RESYNC'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'RESYNC':
            self.testCounter20second_enable = True
            self.requestedRelay = 'PCC'
            self.requestedAction = 'CLOSE'
            if (self.testCounter20second >= 100 and
                    self.relayStatus['F1PCC']['status'] == 'connected' and
                    self.relayStatus['F2PCC']['status'] == 'connected' and
                    self.relayStatus['F3PCC']['status'] == 'connected'):
                self.nextTestState = 'GRID-TIE'
                self.testCounter20second_enable = False
        elif self.currentTestState == 'GRID-TIE':
            pass

        self.currentTestState = self.nextTestState

        if True:
            if self.display_counter_Q >= msgcounterLimit:
                self.display_counter_Q = 0
                self.logger.info(f"{helper.Yellow} test state {self.currentTestState} {helper.reset}")
            self.display_counter_Q = self.display_counter_Q + 1

        msg = {'sender': 'operator', 'currentState': self.currentTestState}
        if msg['sender'] in self.mqtt_counters:
            self.mqtt_counters[msg['sender']] = self.mqtt_counters[msg['sender']] + 1
        else:
            self.mqtt_counters[msg['sender']] = 0

        # sending out messages every 1 second
        if self.mqtt_counters[msg['sender']] >= 5:
            del self.mqtt_counters[msg['sender']]
            msg["schema_name"] = "OperatorMsg"
            self.mqtt_pub.send_pyobj(msg)

"""
Created on Mar 14, 2017
@author: riaps
"""
import capnp
import os
import time
import zmq

from riaps.run.comp import Component
from riaps.interfaces.modbus.config import load_config_file
import riaps.interfaces.modbus.device_capnp as msg_struct

import riaps_capnp

import applibs.constants as const
import applibs.helper as helper
import applibs.applicationPY as apy
from applibs.log_preprocessor import log_json

''' Enable debugging to gather timing information on the code execution'''
debugMode = helper.debugMode


class ComputationalComponent(Component):
    def __init__(self, config, Ts, topology_config):

        super().__init__()
        self.pid = os.getpid()
        self.appInitReady = False
        self.appInitCounter = 0

        # Configure the component from the configuration file
        modbus_device_config = load_config_file(config)
        self.device_name = modbus_device_config["Name"]
        self.powerRating = modbus_device_config['Rating']
        self.nominalVoltage = modbus_device_config['nominalVoltage']
        self.nominalFrequency = modbus_device_config["nominalFrequency"]
        cost_func_params = modbus_device_config['CostFunction']
        self.uuid = modbus_device_config["uuid"]
        self.pccRelayID = modbus_device_config['Feeder']
        self.DOWNSTREAM_RELAYS = modbus_device_config['DOWNSTREAM_RELAYS']

        topology_cfg = load_config_file(topology_config)
        self.DIRECTLY_CONNECTED_RELAYS = topology_cfg['DIRECTLY_CONNECTED_RELAYS'][self.pccRelayID]

        self.group_members: list = []  # This comes from the GROUP_MANAGER via the FSM
        self.pccRelay_closed = None  # None because unknown initially

        self.CONTROL = 0

        '''algorithm variables - estimated voltage '''
        self.estimateVoltagePU = 0

        '''algorithm variables - cost function factor'''
        self.costFunction = [cost_func_params['a'], cost_func_params['b'], cost_func_params['c']]

        '''algorithm variables - initial power command '''
        self.activePowerCommand = 0
        self.initialActivePowerCommand = modbus_device_config['Initial_real_power']
        self.initialReactivePowerCommand = modbus_device_config['Initial_reactive_power']
        self.initialPowerCommand = [self.initialActivePowerCommand, self.initialReactivePowerCommand]

        '''console variables'''
        self.sec_en = 0
        self.angle_en = 0
        self.Ts = Ts

        ''' variables for regulation service DG '''
        self.pinningDG = 0
        self.pinningDG = modbus_device_config["VoltageRegulateDG"]
        self.powerDiffRegulation = 0
        self.regulationPower = [const.default_regulation_active_power,
                                const.default_regulation_reactive_power]

        ''' APP and CONSENSUS CLASS '''
        # distributed voltage estimation app
        self.estimateApp = apy.VoltageEstimation('dynamic', self.Ts, debugMode, logger=self.logger)
        self.estimateApp.consensus.setGains(const.consensus_gain)

        # Resycnhronizaztion to the Grid
        self.resyncApp = apy.ResynchronizationControl('aver', [self.nominalFrequency, self.nominalVoltage], self.Ts,
                                                      debugMode, logger=self.logger)
        self.resyncApp.consensus.setGains((const.active_pwr_ctrl_gain, const.reactive_pwr_ctrl_gain),
                                          (const.freq_ctrl_gain, const.voltage_ctrl_gain_relay))

        # Reconfiguration app to close relay
        self.reconfigRelayCloseApp = apy.RelayCloseControl('aver', [self.nominalFrequency, self.nominalVoltage],
                                                           self.Ts,
                                                           debugMode, logger=self.logger)
        self.reconfigRelayCloseApp.consensus.setGains((const.active_pwr_ctrl_gain, const.reactive_pwr_ctrl_gain),
                                                      (const.freq_ctrl_gain, const.voltage_ctrl_gain_relay))

        # Reconfiguration app to open relay
        self.reconfigRelayOpenApp = apy.RelayOpenControl('aver', [self.nominalFrequency, self.nominalVoltage],
                                                         self.initialPowerCommand, None,
                                                         self.Ts, debugMode, logger=self.logger)
        self.reconfigRelayOpenApp.consensus.setGains((const.active_pwr_ctrl_gain, const.reactive_pwr_ctrl_gain),
                                                     (const.relay_p_ctrl_gain, const.relay_q_ctrl_gain))

        # secondary control app, frequency and voltage regulation
        self.secondApp = apy.SecondaryControl('aver', [self.nominalFrequency, self.nominalVoltage], self.Ts,
                                              debugMode, logger=self.logger)
        self.secondApp.consensus.setGains((const.active_pwr_ctrl_gain, const.reactive_pwr_ctrl_gain),
                                          (const.freq_ctrl_gain, const.voltage_ctrl_gain_island))

        # POI power control app, with economic dispatch
        self.economicApp = apy.EconomicDispatch('aver', self.costFunction, self.Ts,
                                                debugMode, logger=self.logger)
        self.economicApp.consensus.setGains((const.alpha_x_gain, const.edp_reactive_pwr_ctrl_gain),
                                            (const.eps_reg_gain, const.pcc_reactive_pwr_ctrl_gain))

        self.activeFrequencyAndVoltageShift = [0.0, 0.0]
        self.commandParams = []
        self.commandValues = []

        self.consensus_data = {}
        self.relayMessages = {}
        self.currentState = 'RESET'
        self.oldState = 'RESET'
        self.stateBreaker = 'NONE'

        self.msgcounter = 0

        self.logger.info(f"ComputationalComponent: {str(self.pid)} - starting")
        log_json(self.logger, "info", f"{str(self.pid)} - starting", event="COMPONENT_STARTING")

    def on_state_sub(self):
        msg_bytes = self.state_sub.recv()
        msg = riaps_capnp.StateMsg.from_bytes(msg_bytes).to_dict()
        if msg.get("sender") != self.uuid:
            self.logger.debug(f"Ignore state messages from other devices")
            return

        if debugMode:
            self.logger.info(f"{helper.BrightRed}\n"
                             f"PWR_MANAGER - ComputationalComponentAll.py - on_state_sub\n"
                             f"msg: {msg}"
                             f"{helper.RESET}")

        self.currentState = msg.get('currentState')
        self.stateBreaker = msg.get('breaker')

        if self.group_members != msg.get("group"):
            log_json(self.logger, "info", f"Group members changed from {self.group_members} to {msg.get('group')}",
                     event={"name": "GROUP_MEMBERS_CHANGED",
                            "old_group_members": self.group_members,
                            "new_group_members": msg.get('group')})
            self.group_members = msg.get("group")

    def on_relay_sub(self):
        msg_bytes = self.relay_sub.recv()
        msg = riaps_capnp.RelayMsg.from_bytes(msg_bytes)

        if debugMode:
            self.logger.info(f"{helper.BrightMagenta}\n"
                             f"ComputationalComponentAll.py "
                             f"on_relay_sub \n"
                             f"msg: {msg}"
                             f"{helper.RESET}")

        relayID = msg.sender
        self.relayMessages[relayID] = msg.to_dict()

        # those PCC related values are used in GEN_PWR_MANAGER for testing
        if relayID == self.pccRelayID:
            self.pccRelay_closed = self.relayMessages[relayID]["connected"]

        # The config file specifies which relays are "downstream" of this generator.
        # If the relay is downstream we flip the sign of the measurements.
        # We don't need to check for loops because we only allow generators to control relays that
        # they cannot be isolated from.
        if relayID in self.DOWNSTREAM_RELAYS:
            self.relayMessages[relayID]['freqSlip'] = -msg.freqSlip
            self.relayMessages[relayID]['voltDiff'] = -msg.voltDiff
            self.relayMessages[relayID]['angDiff'] = -msg.angDiff
            self.relayMessages[relayID]['activePower'] = -msg.activePower
            self.relayMessages[relayID]['reactivePower'] = -msg.reactivePower

        # Given a set of feeders

    def on_init_clock(self):
        now = self.init_clock.recv_pyobj()
        self.appInitReady = False
        self.consensus_clock.halt()

        self.appInitCounter += 1
        if self.appInitCounter < 6:
            self.logger.info(f"\nComputationalComponentAll.py - on_init_clock\n"
                             f"app initializing")
            return

        self.appInitReady = True
        self.consensus_clock.launch()
        self.init_clock.halt()
        self.logger.info(f"ComputationalComponentAll.py - on_init_clock | "
                         f"app initialized. Starting consensus_clock")
        log_json(self.logger, "info", f"app initialized. Starting consensus_clock", event="COMPONENT_INITIALIZED")

    def on_consensus_clock(self):
        on_clock_start = time.time()
        now = self.consensus_clock.recv_pyobj()
        if not self.appInitReady:
            return

        msg = msg_struct.DeviceQry.new_message()
        msg.device = self.device_name
        msg.operation = "READ"
        msg.params = ["FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]  # frequency, voltageMag, activePower, reactivePower
        msg.values = [[-1]] * len(msg.params)
        msg.timestamp = time.time()
        self.msgcounter += 1
        msg.msgcounter = self.msgcounter
        msg_bytes = msg.to_bytes()

        if debugMode:
            self.logger.info(f"{helper.qryBlack}\n"
                             f"ComputationalComponent.py - on_consensus_clock \n"
                             f"send qry msgcounter {self.msgcounter} to {self.device_name}\n"
                             f"msg.operation: {msg.operation} \n"
                             f"msg.commands:{msg.params}"
                             f"{helper.RESET}")

        try:
            self.device_qry_port.send(msg_bytes)
        except zmq.ZMQError as e:
            self.logger.info(f"{helper.White}"
                             f"on_device_port queue full: {e}"
                             f"{helper.RESET}")

    # riaps:keep_device_port:begin

    def on_device_qry_port(self):
        msg_bytes = self.device_qry_port.recv()
        msg = msg_struct.DeviceAns.from_bytes(msg_bytes)
        if debugMode:
            self.logger.info(f"{helper.ansBlack}\n"
                             f"ComputationalComponent.py | on_device_qry_port \n"
                             f"recv ans from modbus device: {msg}"
                             f"{helper.RESET}")

        if self.pccRelay_closed is None:
            if debugMode:
                self.logger.warn(f"{helper.Red}\n"
                                 f"ComputationalComponentAll.py - on_device_qry_port \n"
                                 f"state of PCC relay is unknown. Skip control for now?"
                                 f"{helper.RESET}")
            return

        if msg.operation == "WRITE":
            return
        # If the answer is in response to a 'write', do above. Otherwise, do below

        frequency, voltageMag, activePower, reactivePower, vref, wref = [value[0] for value in msg.values]

        activePowerPU = activePower / self.powerRating
        reactivePowerPU = reactivePower / self.powerRating
        voltagePU = voltageMag / self.nominalVoltage

        incremental_cost = self.economicApp.getIncrementalCost([activePower, reactivePower])
        estimated_voltage_share = self.estimateApp.get_estimated_voltage_share(voltagePU)

        self.commandParams = ["CONTROL"]
        self.commandValues = [[self.CONTROL]]

        # Instantiate a new distributed consensus message to share local information with group members
        group_consensus_msg = riaps_capnp.DgGeneralMsg.new_message()
        group_consensus_msg.sender = self.uuid
        group_consensus_msg.timestamp = time.time()
        group_consensus_msg.activePower = activePowerPU
        group_consensus_msg.reactivePower = reactivePowerPU
        group_consensus_msg.incrementalCost = incremental_cost
        # Incremental cost is only used in economic app, will be overwritten by economic app if in economic mode
        group_consensus_msg.estimatedVoltageShare = estimated_voltage_share
        # The estimated Voltage Share is only used in the estimation app,
        # the value will be overwritten by estimation app if in an ACTIVE state.
        group_consensus_msg.msgcounter = self.msgcounter

        # These values are eventually passed to the consensus algorithm,
        # and must all be present, even though some are not used in some apps.
        # TODO: This is not quite true. The apps parse out the necessary values from
        #  myDataValues, so we could just pass those values.
        my_data_values = {
            'frequency': frequency,
            'activePowerPU': activePowerPU,
            'reactivePowerPU': reactivePowerPU,
            'incrementalCost': incremental_cost,
            'estimateVoltageShare': estimated_voltage_share,
            'estimateVoltagePU': self.estimateApp.my_estimated_voltage_per_unit
        }

        self.CONTROL = 0 if self.currentState == 'SHUTDOWN' else 1

        # If the current state is ACTIVE_GRID-TIED, LOCAL-CONTROL, or SHUTDOWN, then CONTROL does not change. Otherwise,
        # it changes to VF mode when islanded
        if self.currentState in ['ACTIVE_GRID-TIED', 'SHUTDOWN'] or \
                (self.currentState == 'LOCAL-CONTROL' and self.pccRelay_closed):
            self.CONTROL = self.CONTROL  # PQ mode when connected to the grid
        else:
            self.CONTROL += 2  # VF mode when islanded

        # If the current state is not an ACTIVE state then reset all apps.
        if 'ACTIVE_' not in self.currentState:
            self.logger.info(f"{helper.White}\n"
                             f"ComputationalComponentAll.py - on_device_qry_port \n"
                             f"No secondary control enabled, sending out default commands. and reset all apps"
                             f"{helper.RESET}")
            self.estimateApp.resetApp()
            self.reconfigRelayCloseApp.resetApp()
            self.reconfigRelayOpenApp.resetApp()
            self.resyncApp.resetApp()
            self.economicApp.resetApp()

            self.secondApp.resetApp()
            self.commandParams += ["FREQUENCY", "VOLTAGE", "REAL_POWER", "REACTIVE_POWER"]
            self.commandValues += [[self.nominalFrequency], [self.nominalVoltage], [self.initialActivePowerCommand],
                                   [self.initialReactivePowerCommand]]

        # do app if in one of the ACTIVE STATES
        else:
            self.logger.info(f"{helper.White}\n"
                             f"ComputationalComponentAll.py - on_device_qry_port \n"
                             f"Secondary control enabled. Compute control action"
                             f"{helper.RESET}")

            # remove data from non group members
            for otherId in self.consensus_data:
                if otherId not in self.group_members:
                    del self.consensus_data[otherId]  # guaranteed to be present because it came from the for loop

            if len(self.consensus_data) == 0:
                #  No consensus data received from peers during this time step.
                #  We do not need to consider the case when there is only one generator
                #  doing secondary control because the system will fall back to local control.
                if debugMode:
                    self.logger.info(f"{helper.White}"
                                     f"ComputationalComponentAll.py - on_device_qry_port"
                                     f"No consensus data received from peers during this time step."
                                     f"{helper.RESET}")
            else:
                if debugMode:
                    self.logger.info(f"{helper.White}\n"
                                     f"ComputationalComponent.py - on_device_qry_port \n"
                                     f"Data received from peers since last device query\n"
                                     f"myDataValues: {my_data_values}\n"
                                     f"consensus_data: {self.consensus_data}\n"
                                     f"voltagePU: {voltagePU}\n"
                                     f"{helper.RESET}")

                # always run voltage estimation algorithm
                self.estimateApp.run(my_data_values, self.consensus_data, voltagePU)
                self.estimateVoltagePU = self.estimateApp.my_estimated_voltage_per_unit
                # we don't need to update the myDataValues dictionary because
                # it will be updated in the next iteration of the loop
                group_consensus_msg.estimatedVoltageShare = self.estimateApp.get_estimated_voltage_share()
                # we do need to update the group_consensus_msg because it will be sent out
                # in this iteration of the loop

                # select app based on state machine
                self.logger.info(f"{helper.BrightYellow}\n"
                                 f"ComputationalComponent.py - on_device_qry_port \n"
                                 f"currentState: {self.currentState}\n"
                                 f"self.relayMessages: {self.relayMessages}\n"
                                 f"self.stateBreaker: {self.stateBreaker}"
                                 f"{helper.RESET}")

                if self.currentState == 'ACTIVE_GRID-TIED':
                    # If we just entered this state, then we should reset
                    #  the other apps use the frequency and voltage shift, so they don't need to be reset.
                    if self.oldState != 'ACTIVE_GRID':
                        self.estimateApp.resetApp()
                    power_command = [activePower, reactivePower]

                    self.economicApp.run(my_data_values, self.consensus_data, self.relayMessages[self.pccRelayID],
                                         self.regulationPower, self.pinningDG, power_command)
                    group_consensus_msg.incrementalCost = self.economicApp.getIncrementalCost()
                    # Get the incremental cost from the economic app and add it to the group consensus message.
                    self.commandParams += self.economicApp.commandParams
                    self.commandValues += self.economicApp.commandValues
                    self.oldState = self.currentState
                    self.logger.info(f"{helper.BrightYellow}\n"
                                     f"ComputationalComponent.py - on_device_qry_port \n"
                                     f"Run economicApp\n"
                                     f"commandParams: {self.commandParams}\n"
                                     f"commandValues: {self.commandValues}"
                                     f"{helper.RESET}")
                elif self.currentState == 'ACTIVE_PREPARE-CONNECT':
                    if self.stateBreaker in self.relayMessages:
                        
                        self.reconfigRelayCloseApp.run(my_data_values, self.consensus_data,
                                                       self.relayMessages[self.stateBreaker],
                                                       self.pinningDG, self.activeFrequencyAndVoltageShift,
                                                       self.stateBreaker in self.DIRECTLY_CONNECTED_RELAYS)
                        self.activeFrequencyAndVoltageShift = self.reconfigRelayCloseApp.frequencyAndVoltageOffset
                        self.commandParams += self.reconfigRelayCloseApp.commandParams
                        self.commandValues += self.reconfigRelayCloseApp.commandValues
                        self.logger.info(f"{helper.BrightYellow}\n"
                                         f"ComputationalComponent.py - on_device_qry_port \n"
                                         f"Run reconfigRelayCloseApp \n"
                                         f"commandParams: {self.commandParams}\n"
                                         f"commandValues: {self.commandValues}"
                                         f"{helper.RESET}")
                        
                    self.oldState = self.currentState
                elif self.currentState in ['ACTIVE_PREPARE-DISCONNECT', 'ACTIVE_PREPARE-ISLAND']:
                    if self.stateBreaker in self.relayMessages:
                        if self.oldState not in ['ACTIVE_PREPARE-DISCONNECT', 'ACTIVE_PREPARE-ISLAND']:
                            #  Computing the initial value for activeFrequencyAndVoltageShift is required in order to
                            #  have a smooth transition to the prepareIsland mode because the control is changing
                            #  from P/Q in the economic app to V/F in the reconfigRelayOpenControl app and P/Q is then
                            #  computed by the Opal simulator. If V/F is not initialized properly, then it is possible
                            #  to have a large jump in the power output of the generator when the transition occurs.
                            #  The initial value of activeFrequencyAndVoltageShift needs to be:
                            #  [frequency-self.nominalFrequency, voltageMag-self.nominalVoltage],
                            #  where frequency and voltage are the FV reference values that are input into the
                            #  HWController_Diesel_GenSet_4MVA
                            active_frequency_and_voltage_shift = [(wref - 1) * self.nominalFrequency,
                                                                  (vref - 1) * self.nominalVoltage]
                            self.logger.info(f"{helper.BrightYellow}\n"
                                             f"ComputationalComponent.py - on_device_qry_port \n"
                                             f"initialize reconfigRelayOpenApp"
                                             f"prior FV shift: {self.activeFrequencyAndVoltageShift}"
                                             f"initial FV shift: {active_frequency_and_voltage_shift}"
                                             f"{helper.RESET}")
                            self.activeFrequencyAndVoltageShift = active_frequency_and_voltage_shift

                        self.reconfigRelayOpenApp.run(my_data_values, self.consensus_data,
                                                      self.relayMessages[self.stateBreaker],
                                                      self.pinningDG, self.activeFrequencyAndVoltageShift,
                                                      self.stateBreaker in self.DIRECTLY_CONNECTED_RELAYS)

                        self.logger.info(f"{helper.BrightYellow}\n"
                                         f"ComputationalComponent.py - on_device_qry_port \n"
                                         f"reconfigRelayOpenApp "
                                         f"old FV shift: {self.activeFrequencyAndVoltageShift} "
                                         f"new FV shift: {self.reconfigRelayOpenApp.frequencyAndVoltageOffset}"
                                         f"{helper.RESET}")

                        self.activeFrequencyAndVoltageShift = self.reconfigRelayOpenApp.frequencyAndVoltageOffset
                        self.commandParams += self.reconfigRelayOpenApp.commandParams
                        self.commandValues += self.reconfigRelayOpenApp.commandValues
                        self.logger.info(f"{helper.BrightYellow}\n"
                                         f"ComputationalComponent.py - on_device_qry_port \n"
                                         f"Run reconfigRelayOpenApp \n"
                                         f"commandParams: {self.commandParams}\n"
                                         f"commandValues: {self.commandValues}"
                                         f"{helper.RESET}")
                    self.oldState = self.currentState

                elif self.currentState == 'ACTIVE_PREPARE-RESYNC':
                    self.resyncApp.run(my_data_values, self.consensus_data, self.relayMessages[self.pccRelayID],
                                       self.pinningDG, self.activeFrequencyAndVoltageShift)
                    self.activeFrequencyAndVoltageShift = self.resyncApp.frequencyAndVoltageOffset
                    self.commandParams += self.resyncApp.commandParams
                    self.commandValues += self.resyncApp.commandValues
                    self.oldState = self.currentState

                    # re-initialize economic dispatch for grid-connected mode
                    self.initialPowerCommand = [activePower, reactivePower]
                    self.economicApp.powerInitializedFlag = False

                    self.logger.info(f"{helper.BrightYellow}\n"
                                     f"ComputationalComponent.py - on_device_qry_port \n"
                                     f"Run resyncApp\n"
                                     f"commandParams: {self.commandParams} \n"
                                     f"commandValues: {self.commandValues}"
                                     f"{helper.RESET}")
                elif self.currentState == 'ACTIVE_ISLANDED':
                    if True:
                        if self.oldState == 'ACTIVE_PREPARE-DISCONNECT' and self.reconfigRelayOpenApp.usePowerCommand:
                            self.activeFrequencyAndVoltageShift = [0.0, 0.0]
                        self.secondApp.run(my_data_values, self.consensus_data, self.pinningDG,
                                           self.activeFrequencyAndVoltageShift)
                        self.activeFrequencyAndVoltageShift = self.secondApp.frequencyAndVoltageOffset
                        self.commandParams += self.secondApp.commandParams
                        self.commandValues += self.secondApp.commandValues
                    self.oldState = self.currentState
                    self.logger.info(f"{helper.BrightYellow}\n"
                                     f"ComputationalComponent.py - on_device_qry_port \n"
                                     f"Run secondApp\n"
                                     f"commandParams: {self.commandParams} \n"
                                     f"commandValues: {self.commandValues}"
                                     f"{helper.RESET}")
                else:
                    self.logger.warn(f"No app is selected, this should NOT happen (or should set to default commands?)")

        self.consensus_data.clear()

        # send write command to device
        msg = msg_struct.DeviceQry.new_message()
        msg.device = self.device_name
        msg.operation = "WRITE"
        msg.params = self.commandParams
        msg.values = self.commandValues
        msg.timestamp = time.time()
        msg.msgcounter = self.msgcounter
        msg_bytes = msg.to_bytes()

        if debugMode:
            self.logger.info(f"{helper.BrightYellow}\n "
                             f"ComputationalComponent.py - on_device_qry_port \n"
                             f"WRITE Control Values to device_qry_port msg: {msg}"
                             f"{helper.RESET}")

            self.logger.info(f"GET HWM: {self.device_qry_port.get_hwm()}")

        try:
            self.device_qry_port.send(msg_bytes)
        except zmq.ZMQError as e:
            self.logger.info(f"{helper.Red}"
                             f"on_device_port queue full: {e}"
                             f"{helper.RESET}")

        # update timestamp for group consensus message
        group_consensus_msg.timestamp = time.time()
        if debugMode:
            self.logger.info(f"{helper.localBrightCyan} \n"
                             f"ComputationalComponent.py - on_device_qry_port \n"
                             f"consensus_pub msg: {group_consensus_msg}"
                             f"{helper.RESET}")
        try:
            msg_bytes = group_consensus_msg.to_bytes()
            self.consensus_pub.send(msg_bytes)
        except zmq.ZMQError as e:
            self.logger.info(f"{helper.White}"
                             f"consensus_pub queue full: {e}"
                             f"{helper.RESET}")

        on_clock_end = time.time()

    def on_consensus_sub(self):
        msg_bytes = self.consensus_sub.recv()
        msg = riaps_capnp.DgGeneralMsg.from_bytes(msg_bytes)

        if msg.sender == self.uuid:
            return

        otherId = msg.sender
        otherTimestamp = msg.timestamp
        otherValue_activePower = msg.activePower
        otherValue_reactivePower = msg.reactivePower
        otherValue_incrementalCost = msg.incrementalCost
        othervalue_estimatedVoltageShare = msg.estimatedVoltageShare

        if debugMode:
            self.logger.info(f"{helper.BrightCyan}"
                             f"ComputationalComponent.py \n"
                             f"on_consensus_sub \n"
                             f"msg: {msg}\n"
                             f"Is {otherId} in the group members list?: {self.group_members}"
                             f"{helper.RESET}")

        if otherId in self.group_members:  # self.uuid was used for general operation
            self.consensus_data[otherId] = {
                'activePowerPU': otherValue_activePower,
                'reactivePowerPU': otherValue_reactivePower,
                'incrementalCost': otherValue_incrementalCost,
                'estimateVoltageShare': othervalue_estimatedVoltageShare
            }

    def __destroy__(self):
        self.logger.info(f"[{self.pid}] destroyed")

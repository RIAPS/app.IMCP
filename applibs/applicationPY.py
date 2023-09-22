'''
Created on Sep 28, 2021
@author: Hao Tu

Consensus-based applications for microgrid control
'''

import applibs.consensusPY as cpy
import applibs.helper as helper


class ResynchronizationControl:
    def __init__(self, consensusType='aver', nominalFrequencyAndVoltage=None, Ts=0.2, debugMode=False, logger=None):

        if consensusType == 'aver':
            self.consensus = cpy.AverageConsensus(numberOfVariable=2, Ts=Ts, debugMode=debugMode, logger=logger)
        else:
            pass
        if nominalFrequencyAndVoltage is None:
            nominalFrequencyAndVoltage = [60, 480]

        self.frequencyAndVoltageOffset = [0.0, 0.0]
        # application specific variables.
        self.myPq = ()
        self.pqlist = []
        self.fvlist = []
        self.commandValues = []
        self.commandParams = []
        self.nominalFrequencyAndVoltage = nominalFrequencyAndVoltage
        self.relayFrequencyDiff = 0
        self.relayVoltageDiff = 0
        self.relayAngleDiff = 0
        self.Ts = Ts
        self.logger = logger

    def run(self, myDataDict, DgDataDict, relayDataDict, pinning, initialConsensusVariable):
        # set initial consensus variable for transition between different apps
        self.consensus.setConsensusVariable(initialConsensusVariable)

        # get the pq information assuming p and q for consensus
        self.myPq = (myDataDict['activePowerPU'], myDataDict['reactivePowerPU'])
        self.pqlist = [(DgDataDict[dguuid]['activePowerPU'], DgDataDict[dguuid]['reactivePowerPU']) for dguuid in
                       DgDataDict]
        # get relay info
        self.relayFrequencyDiff = relayDataDict['freqSlip']
        self.relayVoltageDiff = relayDataDict['voltDiff']
        self.relayAngleDiff = relayDataDict['angDiff']

        self.fvlist = [self.relayFrequencyDiff + self.relayAngleDiff / 1666.666667, self.relayVoltageDiff]
        self.frequencyAndVoltageOffset = self.consensus.run(self.myPq, self.pqlist, self.fvlist, pinning)
        self.commandValues = [[sum(i)] for i in zip(self.frequencyAndVoltageOffset, self.nominalFrequencyAndVoltage)]
        self.commandParams = ["FREQUENCY", "VOLTAGE"]

    def resetApp(self):
        self.consensus.resetConsensusVariable()


class EconomicDispatch():
    def __init__(self, consensusType='aver', costFunction=None, Ts=0.2, debugMode=False, logger=None):

        if consensusType == 'aver':
            self.consensus = cpy.AverageConsensus(numberOfVariable=2, Ts=Ts, debugMode=debugMode, logger=logger)
        else:
            pass
        if costFunction is None:
            costFunction = [1, 1, 1]
        self.costFunction = costFunction
        self.powerInitializedFlag = False
        self.Ts = Ts
        self.logger = logger

        # application specific variables.
        self.incrementalCostlist = []
        self.regulationList = []
        self.commandValues = []
        self.commandParams = []
        self.pccRelayActivePower = 0
        self.pccRelayReactivePower = 0

    def run(self, myDataDict, DgDataDict, relayDataDict, regulationPower, pinning, initial_power_command: list):

        # The consensus input is the incremental cost and reactive power
        my_consensus_input = (self.getIncrementalCost(initial_power_command),
                              myDataDict['reactivePowerPU'])
        # If app has not been initialized, the call to getIncrementalCost()
        # will initialize the app.

        self.incrementalCostlist = [(DgDataDict[dguuid]['incrementalCost'],
                                     DgDataDict[dguuid]['reactivePowerPU']) for
                                    dguuid in DgDataDict]

        # get relay info
        self.pccRelayActivePower = relayDataDict['activePower']
        self.pccRelayReactivePower = relayDataDict['reactivePower']
        # get the regulation power
        regulationActivePower = regulationPower[0]
        regulationReactivePower = regulationPower[1]

        self.regulationList = [regulationActivePower - self.pccRelayActivePower,
                               regulationReactivePower - self.pccRelayReactivePower]

        edpCommand = self.consensus.run(my_consensus_input,
                                        self.incrementalCostlist,
                                        self.regulationList,
                                        pinning)
        # The consensus variable is not returned by the consensus algorithm.
        # It is stored in the consensus algorithm as a class variable called consensusVariable.

        self.commandValues = [[(edpCommand[0] - self.costFunction[1]) / self.costFunction[0] / 2], [edpCommand[1]]]
        self.commandParams = ["REAL_POWER", "REACTIVE_POWER"]

    def setInitialIncrementalCost(self, initial_power_command):
        # cost function is a quadratic function of active power
        # the incremental cost is the derivative of the cost function
        initial_incremental_cost = 2 * initial_power_command[0] * self.costFunction[0] + self.costFunction[1]
        initial_reactive_power = initial_power_command[1]
        self.consensus.setConsensusVariable([initial_incremental_cost, initial_reactive_power])

    def getIncrementalCost(self, initial_power_command=None):
        if not self.powerInitializedFlag and initial_power_command is not None:
            self.setInitialIncrementalCost(initial_power_command)
            self.powerInitializedFlag = True
        # The incremental cost is the first element of the consensus variable
        consensus_variable = self.consensus.getConsensusVariable()
        return consensus_variable[0]

    def getInitializedFlag(self):
        return self.powerInitializedFlag

    def resetApp(self):
        self.powerInitializedFlag = False
        self.consensus.resetConsensusVariable()


class RelayCloseControl:
    def __init__(self, consensusType='aver', nominalFrequencyAndVoltage=None, Ts=0.2, debugMode=False, logger=None):

        if consensusType == 'aver':
            self.consensus = cpy.AverageConsensus(numberOfVariable=2, Ts=Ts, debugMode=debugMode, logger=logger)
        else:
            pass
        if nominalFrequencyAndVoltage is None:
            nominalFrequencyAndVoltage = [60, 480]

        self.frequencyAndVoltageOffset = [0.0, 0.0]
        # application specific variables.
        self.myPq = ()
        self.pqlist = []
        self.fvlist = []
        self.commandValues = []
        self.commandParams = []
        self.nominalFrequencyAndVoltage = nominalFrequencyAndVoltage
        self.FrequencyDiff = 0
        self.relayVoltageDiff = 0
        self.relayAngleDiff = 0
        self.Ts = Ts
        self.logger = logger

    def run(self,
            myDataDict,
            DgDataDict,
            relayDataDict,
            pinning,
            initialConsensusVariable,
            requested_relay_is_directly_connected):
        # set initial consensus variable for transition between different apps
        self.consensus.setConsensusVariable(initialConsensusVariable)

        # get the pq information assuming p and q for consensus
        self.myPq = (myDataDict['activePowerPU'], myDataDict['reactivePowerPU'])
        self.pqlist = [(DgDataDict[dguuid]['activePowerPU'], DgDataDict[dguuid]['reactivePowerPU']) for dguuid in
                       DgDataDict]
        # get relay info
        self.FrequencyDiff = myDataDict['frequency'] - self.nominalFrequencyAndVoltage[0]
        self.relayVoltageDiff = relayDataDict['voltDiff']
        self.relayAngleDiff = relayDataDict['angDiff']

        # We only want to have this generator control the relay if it cannot be isolated from this generator.
        # The reason is that otherwise we have to concern ourselves with loops in the network and the need to compute
        # whether the generator is to the left or right of the relay.
        # The generator config file specifies it's PCC relay. If the id of the relay is in the list of
        # DIRECTLY_CONNECTED_RELAYS in the topology config file for this generator's PCC then we know that it cannot be
        # isolated from this generator. If it can be isolated then we don't want to control it.
        if not requested_relay_is_directly_connected:
            self.fvlist = [0, 0]
            return
        self.fvlist = [self.FrequencyDiff + self.relayAngleDiff / 1666.666667, self.relayVoltageDiff]
        # 1666.666667 is a conversion factor from angle difference to frequency difference.
        self.frequencyAndVoltageOffset = self.consensus.run(self.myPq, self.pqlist, self.fvlist, pinning)
        self.commandValues = [[sum(i)] for i in zip(self.frequencyAndVoltageOffset, self.nominalFrequencyAndVoltage)]
        self.commandParams = ["FREQUENCY", "VOLTAGE"]


    def resetApp(self):
        self.consensus.resetConsensusVariable()


class RelayOpenControl:
    def __init__(self, consensusType='aver', nominalFrequencyAndVoltage=None, nominalActiveAndReactivePower=None,
                 droop_gains=None, Ts=0.2, debugMode=False, logger=None):

        if consensusType == 'aver':
            self.consensus = cpy.AverageConsensus(numberOfVariable=2, Ts=Ts, debugMode=debugMode, logger=logger)
        else:
            pass

        # These values are used if the configuration file does not have the values.
        if nominalFrequencyAndVoltage is None:
            nominalFrequencyAndVoltage = [60, 480]
        if nominalActiveAndReactivePower is None:
            nominalActiveAndReactivePower = [500, 100]
        if droop_gains is None:
            if nominalFrequencyAndVoltage[1] < 500:
                droop_gains = [6.28 / 1000000 * 1000, 20 / 200000 * 1000]
            else:
                droop_gains = [6.28 / 1000000 * 1000, 20 / 200000 * 1000]

        self.frequencyAndVoltageOffset = [0.0, 0.0]
        # application specific variables.
        self.usePowerCommand = True
        self.myPq = ()
        self.pqlist = []
        self.regulationList = []
        self.commandValues = []
        self.commandParams = []
        self.nominalFrequencyAndVoltage = nominalFrequencyAndVoltage
        self.nominalActiveAndReactivePower = nominalActiveAndReactivePower
        self.droop_gains = droop_gains
        self.RelayActivePower = 0
        self.RelayReactivePower = 0
        self.Ts = Ts
        self.logger = logger

    def run(self,
            myDataDict,
            DgDataDict,
            relayDataDict,
            pinning,
            initialConsensusVariable,
            requested_relay_is_directly_connected):
        # set initial consensus variable for transition between different apps

        self.consensus.setConsensusVariable(initialConsensusVariable)

        # get the pq information assuming p and q for consensus
        self.myPq = (myDataDict['activePowerPU'], myDataDict['reactivePowerPU'])
        self.pqlist = [(DgDataDict[dguuid]['activePowerPU'], DgDataDict[dguuid]['reactivePowerPU']) for dguuid in
                       DgDataDict]
        # get relay info
        self.RelayActivePower = relayDataDict['activePower']
        self.RelayReactivePower = relayDataDict['reactivePower']
        # regulation power are always 0 for open relay control
        regulationActivePower = 0
        regulationReactivePower = 0

        # We only want to have this generator control the relay if it cannot be isolated from this generator.
        # The reason is that otherwise we have to concern ourselves with loops in the network and the need to compute
        # whether the generator is to the left or right of the relay.
        # The generator config file specifies it's PCC relay. If the id of the relay is in the list of
        # DIRECTLY_CONNECTED_RELAYS in the topology config file for this generator's PCC then we know that it cannot be
        # isolated from this generator. If it can be isolated then we don't want to control it.
        if not requested_relay_is_directly_connected:
            self.regulationList = [0, 0]
            return

        self.regulationList = [regulationActivePower - self.RelayActivePower,
                               regulationReactivePower - self.RelayReactivePower]
        self.frequencyAndVoltageOffset = self.consensus.run(self.myPq, self.pqlist, self.regulationList, pinning)
        self.commandValues = [[sum(i)] for i in
                              zip(self.frequencyAndVoltageOffset, self.nominalFrequencyAndVoltage)]
        self.commandParams = ["FREQUENCY", "VOLTAGE"]
        self.usePowerCommand = False

    def resetApp(self):
        self.consensus.resetConsensusVariable()


class SecondaryControl:
    def __init__(self, consensusType='aver', nominalFrequencyAndVoltage=None, Ts=0.2, debugMode=False, logger=None):

        if consensusType == 'aver':
            self.consensus = cpy.AverageConsensus(numberOfVariable=2, Ts=Ts, debugMode=debugMode, logger=logger)
        else:
            pass
        if nominalFrequencyAndVoltage is None:
            nominalFrequencyAndVoltage = [60, 480]

        self.frequencyAndVoltageOffset = [0.0, 0.0]
        # application specific variables.
        self.myPq = ()
        self.pqlist = []
        self.fvlist = []
        self.commandValues = []
        self.commandParams = []
        self.nominalFrequencyAndVoltage = nominalFrequencyAndVoltage
        self.FrequencyDiff = 0
        self.VoltageDiff = 0
        self.Ts = Ts
        self.logger = logger

    def run(self, myDataDict, DgDataDict, pinning, initialConsensusVariable):
        # set consensus variable for transition between different apps
        self.consensus.setConsensusVariable(initialConsensusVariable)

        # get the pq information assuming p and q for consensus
        self.myPq = (myDataDict['activePowerPU'], myDataDict['reactivePowerPU'])
        self.pqlist = [(DgDataDict[dguuid]['activePowerPU'], DgDataDict[dguuid]['reactivePowerPU']) for dguuid in
                       DgDataDict]
        # get relay info
        self.FrequencyDiff = myDataDict['frequency'] - self.nominalFrequencyAndVoltage[0]
        self.VoltageDiff = (myDataDict['estimateVoltagePU'] - 1.0 / 1.732)
        # 1.732 is the sqrt(3) when you convert from line-to-line voltage to line-to-neutral voltage

        self.fvlist = [self.FrequencyDiff, self.VoltageDiff]
        self.frequencyAndVoltageOffset = self.consensus.run(self.myPq, self.pqlist, self.fvlist, pinning)
        self.commandValues = [[sum(i)] for i in zip(self.frequencyAndVoltageOffset, self.nominalFrequencyAndVoltage)]
        self.commandParams = ["FREQUENCY", "VOLTAGE"]

    def resetApp(self):
        self.consensus.resetConsensusVariable()


class VoltageEstimation:
    def __init__(self, consensusType='dynamic', Ts=0.2, debugMode=False, logger=None):

        self.consensusType = consensusType
        if consensusType == 'dynamic':
            self.consensus = cpy.DynamicConsensus(numberOfVariable=1, Ts=Ts, debugMode=debugMode, logger=logger)
        elif consensusType == 'ramp-dynamic':
            self.consensus = cpy.RampDynamicConsensus(numberOfVariable=1, Ts=Ts, debugMode=debugMode, logger=logger)
        else:
            pass
        # application specific variables.
        self.my_estimated_voltage_share = ()
        self.my_estimated_voltage_per_unit = 0
        self.voltageInitializedFlag = False
        self.Ts = Ts
        self.logger = logger

    def run(self, myDataDict, DgDataDict, measuredVoltage):
        # Initialize the voltage estimation app on the first run call.
        if not self.voltageInitializedFlag:
            self.voltageInitializedFlag = True
            self.initialize_app(measuredVoltage)

        # get the voltage information
        # my_consensus_input = (myDataDict['estimateVoltageShare'])
        my_consensus_input = self.consensus.outputValues
        peers_consensus_input = [DgDataDict[dguuid]['estimateVoltageShare'] for dguuid in DgDataDict]
        consensus_output = self.consensus.run(my_consensus_input,
                                              peers_consensus_input,
                                              measuredVoltage)
        self.my_estimated_voltage_per_unit = consensus_output[0]
        self.logger.info(f"{helper.Green} "
                         f"Estimated voltage per unit: {self.my_estimated_voltage_per_unit}"
                         f"{helper.RESET}")

        # for testing purpose only
        peers_estimated_voltage = [DgDataDict[dguuid]['estimateVoltageShare'][0] for dguuid in DgDataDict]
        voltage_list = peers_estimated_voltage + [self.my_estimated_voltage_per_unit]
        averageVoltage = sum(voltage_list) / len(voltage_list)
        # self.logger.info(f"{helper.Green} Average voltage at this time step: {averageVoltage}{helper.RESET}")

    def resetApp(self):
        self.consensus.resetConsensusVariable()
        self.voltageInitializedFlag = False

    def get_estimated_voltage_share(self, initial_voltage_share=None):
        # if the consensus output is not initialized, initialize it with the initial voltage share
        if not self.consensus.outputValues and initial_voltage_share is not None:
            self.initialize_app(initial_voltage_share)
        return self.consensus.outputValues

    def initialize_app(self, measured_voltage):
        self.my_estimated_voltage_per_unit = measured_voltage
        if self.consensusType == 'dynamic':
            self.my_estimated_voltage_share = [measured_voltage]
        else:
            self.my_estimated_voltage_share = [measured_voltage, measured_voltage]
        self.consensus.setOutputValues(self.my_estimated_voltage_share)


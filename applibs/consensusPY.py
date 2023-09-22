'''
Created on Sep 28, 2021
@author: Hao Tu

Consensus algorithms for microgrid control applications
'''

import numpy as np
import applibs.helper as helper

msgcounterLimit = helper.msgcounterLimit


class AverageConsensus():
    def __init__(self, numberOfVariable=1, Ts=0.2, debugMode=False, logger=None):
        self.numberOfVariable = numberOfVariable
        self.consensusVariable = np.zeros(self.numberOfVariable)
        self.consensusGains = np.zeros(self.numberOfVariable)
        self.piningGains = np.zeros(self.numberOfVariable)
        self.debugMode = debugMode
        self.display_counter_Q = 0
        self.Ts = Ts
        self.logger = logger

    def run(self, myDataValues, dataValues, pinningValues, pinning):

        myDataValues = np.array(myDataValues)
        dataValues = np.array(dataValues)  # [ [P1 Q1]; [P2 Q2] ]
        dataValues = dataValues.T  # [ [P1 P2]; [Q1 Q2] ]
        if pinning == 1:
            pinningValues = np.array(pinningValues)
        else:
            pinningValues = np.zeros(self.numberOfVariable)

        if True:
            if self.display_counter_Q >= msgcounterLimit:
                self.display_counter_Q = 0
                self.logger.info(f"{helper.Cyan}data from others {dataValues}")
                self.logger.info(f"{helper.Cyan}Self consensus variables{self.consensusVariable}")
            self.display_counter_Q += 1

        if self.numberOfVariable == 1:
            sum_otherConsensusVariable = np.sum(dataValues)
            numberOfReceivedInfo = dataValues.shape[0]
        else:
            sum_otherConsensusVariable = np.sum(dataValues, 1)  # this squeezes dimension automatically
            numberOfReceivedInfo = dataValues.shape[1]  # [ P1+P2, Q1+Q2 ]
        der_ConsensusVariable = self.Ts * (
                self.consensusGains * (
                myDataValues * numberOfReceivedInfo - sum_otherConsensusVariable) + pinningValues * self.piningGains)
        self.consensusVariable -= der_ConsensusVariable

        return self.consensusVariable.tolist()

    def setConsensusVariable(self, value):
        self.consensusVariable = np.array(value)

    def resetConsensusVariable(self):
        self.consensusVariable = np.zeros(self.numberOfVariable)

    def setGains(self, consensusGains, piningGains):
        self.consensusGains = np.array(consensusGains)
        self.piningGains = np.array(piningGains)

    def getConsensusVariable(self):
        return self.consensusVariable.tolist()


class DynamicConsensus():
    def __init__(self, numberOfVariable=1, Ts=0.2, debugMode=False, logger=None):
        self.numberOfVariable = numberOfVariable
        self.consensusVariable = np.zeros(self.numberOfVariable)
        self.consensusGains = np.zeros(self.numberOfVariable)
        self.debugMode = debugMode
        self.display_counter_Q = 0
        self.Ts = Ts
        self.logger = logger
        self.outputValues = []

    def run(self, myDataValues, dataValues, trackingInput):

        myDataValues = np.array(myDataValues)
        dataValues = np.array(dataValues)
        dataValues = dataValues.T
        inputValues = np.array(trackingInput)

        if self.numberOfVariable == 1:
            sum_otherConsensusVariable = np.sum(dataValues)
        else:
            sum_otherConsensusVariable = np.sum(dataValues, 1)  # this squeezes dimension automatically

        numberOfReceivedInfo = dataValues.shape[1]

        self.logger.info(f"{helper.White}"
                         f"consensusPY.py run \n"
                         f"self.Ts: {self.Ts} \n"
                         f"self.consensusVariable: {self.consensusVariable} \n"
                         f"self.consensusGains: {self.consensusGains}\n"
                         f"myDataValues: {myDataValues} type: {type(myDataValues)} shape: {myDataValues.shape}\n"
                         f"dataValues: {dataValues} type: {type(dataValues)} shape: {dataValues.shape}\n"
                         f"sum_otherConsensusVariable: {sum_otherConsensusVariable}"
                         f"{helper.RESET}")

        der_ConsensusVariable = self.Ts * (
                self.consensusGains * (myDataValues * numberOfReceivedInfo - sum_otherConsensusVariable))

        self.logger.info(f"{helper.White}"
                         f"consensusPY.py run \n"
                         f"consensus variable: {self.consensusVariable} type: {type(self.consensusVariable)}\n"
                         f"der_ConsensusVariable: {der_ConsensusVariable} type: {type(der_ConsensusVariable)}"
                         f"{helper.RESET}")
        self.consensusVariable += der_ConsensusVariable
        outputValues = inputValues - self.consensusVariable
        self.outputValues = outputValues.tolist()

        return self.outputValues

    def resetConsensusVariable(self):
        self.consensusVariable = np.zeros(self.numberOfVariable)
        self.outputValues = []

    def setGains(self, consensusGains):
        self.consensusGains = np.array(consensusGains)

    def setOutputValues(self, outputValues):
        self.outputValues = outputValues

    def setConsensusVariable(self, value):
        self.consensusVariable = np.array(value)

    def getConsensusVariable(self):
        return self.consensusVariable.tolist()


class RampDynamicConsensus():
    def __init__(self, numberOfVariable=1, Ts=0.2, debugMode=False, logger=None):
        self.numberOfVariable = numberOfVariable
        self.consensusVariablePx = np.zeros(self.numberOfVariable)
        self.consensusVariablePy = np.zeros(self.numberOfVariable)
        self.consensusGainsX = np.zeros(self.numberOfVariable)
        self.consensusGainsY = np.zeros(self.numberOfVariable)
        self.debugMode = debugMode
        self.display_counter_Q = 0
        self.Ts = Ts
        self.logger = logger
        self.outputValues = []

    def run(self, myDataValues, dataValues, trackingInput):

        myDataValuesX = np.array(myDataValues[:self.numberOfVariable])
        myDataValuesY = np.array(myDataValues[self.numberOfVariable:])
        dataValues = np.array(dataValues)
        dataValuesX = dataValues[:, :self.numberOfVariable]
        dataValuesY = dataValues[:, self.numberOfVariable:]
        dataValuesX = np.squeeze(dataValuesX)
        dataValuesY = np.squeeze(dataValuesY)
        dataValuesX = dataValuesX.T
        dataValuesY = dataValuesY.T
        inputValues = np.array(trackingInput)

        if True:
            if self.display_counter_Q >= msgcounterLimit:
                self.display_counter_Q = 0
                self.logger.info(f"{helper.Cyan}dynamic data from others: {dataValuesX} and {dataValuesY} ")
                self.logger.info(
                    f"{helper.Cyan}Self dynamic consensus variables: {self.consensusVariablePx} and {self.consensusVariablePy} ")
            self.display_counter_Q += 1

        if self.numberOfVariable == 1:
            sum_otherConsensusVariableX = np.sum(dataValuesX)
            sum_otherConsensusVariableY = np.sum(dataValuesY)
            numberOfReceivedInfo = dataValuesX.shape[0]
        else:
            sum_otherConsensusVariableX = np.sum(dataValuesX, 1)  # this squeezes dimension automatically
            sum_otherConsensusVariableY = np.sum(dataValuesY, 1)  # this squeezes dimension automatically
            numberOfReceivedInfo = dataValuesX.shape[1]
        der_ConsensusVariablePy = self.Ts * (
                self.consensusGainsY * (myDataValuesY * numberOfReceivedInfo - sum_otherConsensusVariableY))
        der_ConsensusVariablePx = self.Ts * (
                self.consensusGainsX * (myDataValuesX * numberOfReceivedInfo - sum_otherConsensusVariableX)) \
                                  + der_ConsensusVariablePy
        self.consensusVariablePx += der_ConsensusVariablePx
        self.consensusVariablePy += der_ConsensusVariablePy
        outputValuesX = inputValues - self.consensusVariablePx
        outputValuesY = inputValues - self.consensusVariablePy
        outputValuesX = outputValuesX.tolist()
        outputValuesY = outputValuesY.tolist()
        self.outputValues = outputValuesX + outputValuesY

        return outputValuesX

    def resetConsensusVariable(self):
        self.consensusVariablePx = np.zeros(self.numberOfVariable)
        self.consensusVariablePy = np.zeros(self.numberOfVariable)

    def setGains(self, consensusGains):
        self.consensusGainsX = np.array(consensusGains)
        self.consensusGainsY = np.array(consensusGains)

    def setOutputValues(self, outputValues):
        self.outputValues = outputValues

    #def setConsensusVariable(self, value):
    #    self.consensusVariable = np.array(value)

    #def getConsensusVariable(self):
    #    return self.consensusVariable.tolist()

# riaps:keep_import:begin
import capnp

from applibs.ComputationalComponentAll import ComputationalComponent
import applibs.helper as helper

import imcp_capnp
# riaps:keep_import:end

debugMode = helper.debugMode


# riaps:keep_constr:begin
class GEN1_PWR_MANAGER(ComputationalComponent):
    def __init__(self, config, Ts, topology_config):
        super(GEN1_PWR_MANAGER, self).__init__(config, Ts, topology_config)
    # riaps:keep_constr:end

    # riaps:keep_local_event_port:begin
    def on_local_event_port(self):
        local_event = self.local_event_port.recv()
    # riaps:keep_local_event_port:end

    # riaps:keep_consensus_clock:begin
    def on_consensus_clock(self):
        super(GEN1_PWR_MANAGER, self).on_consensus_clock()

    # riaps:keep_consensus_clock:end

    def on_operator_sub(self):
        operator_msg_bytes = self.operator_sub.recv()
        operator_msg = imcp_capnp.OperatorMsg.from_bytes(operator_msg_bytes)

        if debugMode:
            self.logger.info(f"{helper.Cyan}\n"
                             f"GEN1_PWR_MANAGER.py on_operator_sub \n"
                             f"msg: {operator_msg}"
                             f"{helper.RESET}")

        # regulationSignal, regulationSignal2 are the only parameters used here.
        # They correspond to the setpoint for the active and reactive power at the POI to the main grid.
        StartStop_opal, gridBreaker_opal, secondaryCtrl_opal, \
        secondaryAngleCtrl_opal, regulationSignal, regulationSignal2 = operator_msg.opalValues

        # TODO: The max is grid dependent and should be stored in the config and checked. Probably in the operator.
        #  this also depends on the predicted real-time load. We need some logic in the operator to compute safe limits.
        #  we probably also want to make sure the operator cannot create a loop by closing too many breakers.
        # for direct PQ command
        self.regulationPower = [regulationSignal, regulationSignal2]  # regulation power from operator P kW, Q kVar
# riaps:keep_impl:begin

# riaps:keep_impl:end

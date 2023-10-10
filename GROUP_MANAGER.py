# riaps:keep_import:begin
import capnp
import copy
import numpy as np
import imcp_capnp
import time

from riaps.run.comp import Component
import applibs.helper as helper

from riaps.interfaces.modbus.config import load_config_file

debugMode = helper.debugMode


# riaps:keep_import:end


def build_connected_group(my_group_id: int,
                          topology: dict,
                          status_of_relays: dict):
    number_of_groups = len(topology["electrically_independent_groups"])

    identity_matrix = np.diag(np.ones(number_of_groups))
    adjacency_matrix = np.diag(np.zeros(number_of_groups))

    for relay_id, relay_status in status_of_relays.items():
        if relay_status["connected"]:
            index = tuple(topology['groups_connected_by_relay'][relay_id])
            # need to cast to tuple because pyyaml treats value as a list
            adjacency_matrix[index] = 1

    adjacency_matrix = adjacency_matrix + adjacency_matrix.T + identity_matrix
    connection_matrix = np.linalg.matrix_power(adjacency_matrix, number_of_groups - 1)

    connected_group = []
    connected_group_name = ""

    for group_id, connection_status in enumerate(connection_matrix[my_group_id]):
        electrically_independent_group_members = topology["electrically_independent_groups"][group_id]
        electrically_independent_group_name = topology["electrically_independent_group_names"][str(electrically_independent_group_members)]

        if connection_status > 0:
            connected_group_name += electrically_independent_group_name
            connected_group += electrically_independent_group_members

    return sorted(connected_group), connected_group_name


class GROUP_MANAGER(Component):

    # riaps:keep_constr:begin
    def __init__(self, config, topology_config):
        super().__init__()
        self.msg_counter = 0
        self.time_of_last_broadcast = time.time()

        self.commands = []
        self.status_of_relays = {}
        self.requestedRelay = 'NONE'
        self.requestedAction = 'NONE'

        modbus_device_config = load_config_file(config)
        self.device_name = modbus_device_config["Name"]
        self.uuid = modbus_device_config['uuid']
        self.MAX_GROUP_PUBLISH_DELAY_SECONDS = modbus_device_config['MAX_GROUP_PUBLISH_DELAY_SECONDS']

        # group manager variables
        group_config = load_config_file(topology_config)
        self.group_config = group_config
        self.group = []
        self.group_name = ""
        self.future_group = []
        self.future_group_name = ""
        self.electrically_independent_groups = group_config['electrically_independent_groups']
        self.groups_connected_by_relay = group_config['groups_connected_by_relay']

        self.my_group_id = None
        for group_id, group in self.electrically_independent_groups.items():
            if self.uuid in group:
                self.my_group_id = group_id

    def on_relay_sub(self):
        msg_bytes = self.relay_sub.recv()
        msg = imcp_capnp.RelayMsg.from_bytes(msg_bytes)

        if debugMode:
            self.logger.debug(f"{helper.BrightMagenta}"
                              f"GROUP_MANAGER.py | on_relay_sub \n"
                              f"msg: {msg}"
                              f"{helper.RESET}")

        relay_id = msg.sender
        relay_connection_status = {"connected": msg.connected}
        prior_relay_status = self.status_of_relays.get(relay_id, None)
        if relay_connection_status == prior_relay_status:
            relay_status_has_changed = False
        else:
            relay_status_has_changed = True
            self.status_of_relays[relay_id] = relay_connection_status

        now = time.time()
        time_since_last_broadcast = now - self.time_of_last_broadcast

        if relay_status_has_changed or time_since_last_broadcast > self.MAX_GROUP_PUBLISH_DELAY_SECONDS:
            self.time_of_last_broadcast = now

            self.group, self.group_name = self.group_management()
            self.publish_group_msg(timestamp=now)

            if debugMode or (self.group != self.future_group):
                if relay_status_has_changed:
                    reason = f"relay {relay_id} changed from {prior_relay_status} to {relay_connection_status}"
                else:
                    reason = "max time between group updates elapsed "

                self.logger.info(
                    f"{helper.BrightMagenta}"
                    f"GROUP_MANAGER.py | on_relay_sub | publish group update \n"
                    f"reason: {reason} \n"
                    f"current group is {self.group} \n"
                    f"future group is {self.future_group}"
                    f"{helper.RESET}")

    def group_management(self):
        group, group_name = build_connected_group(my_group_id=self.my_group_id,
                                                  topology=self.group_config,
                                                  status_of_relays=self.status_of_relays)
        return group, group_name

    # calculate future group with a single relay with future status
    def future_group_management(self, group, group_name, requested_relay, requested_action):

        if requested_relay == 'NONE' or requested_action not in ['OPEN', 'CLOSE']:
            return group, group_name

        connected_in_future = False if requested_action == 'OPEN' else True

        future_relay_status = copy.deepcopy(self.status_of_relays)
        future_relay_status[requested_relay]["connected"] = connected_in_future

        future_group, future_group_name = build_connected_group(my_group_id=self.my_group_id,
                                                                topology=self.group_config,
                                                                status_of_relays=future_relay_status)

        return future_group, future_group_name

    def on_operator_sub(self):
        operator_msg_bytes = self.operator_sub.recv()
        operator_msg = imcp_capnp.OperatorMsg.from_bytes(operator_msg_bytes)
        if debugMode:
            self.logger.debug(f"{helper.Cyan}\n"
                              f"GROUP_MANAGER.py "
                              f"on_operator_sub \n"
                              f"msg: {operator_msg}"
                              f"{helper.RESET}")

        # This was originally written to allow opening of all PCC relays simultaneously
        # by sending the string "PCC" as the requestedRelay and using the
        # defined self.pccRelayID.
        # Now, it is written to allow opening of only one relay at a time.
        # I foresee a problem with this when a node goes down and recovers because
        # the information about which relays should be open/closed will be lost.
        # We probably need to store the desired state of all relays in the operator
        # and then send that information to the group manager in the operator message.
        # TODO: Future work: store desired state of all relays in operator and send
        self.requestedRelay = operator_msg.requestedRelay
        self.requestedAction = operator_msg.requestedAction
        self.commands = list(operator_msg.opalValues)

        self.future_group, self.future_group_name = self.future_group_management(self.group,
                                                                                 self.group_name,
                                                                                 self.requestedRelay,
                                                                                 self.requestedAction)  # sets self.futureGroup

        self.publish_group_msg(timestamp=time.time())

    def handleActivate(self):
        self.logger.info(f"group manager activate")

    def publish_group_msg(self, timestamp):

        msg = imcp_capnp.GroupMsg.new_message()
        msg.sender = self.device_name
        msg.timestamp = timestamp
        # TODO: There should also be a timestamp for when the state should be reached. See the IMCP_FSM.py
        #  function on_group_sub, the when variable..
        msg.msgcounter = self.msg_counter
        msg.group = self.group
        msg.groupName = self.group_name
        msg.requestedRelay = self.requestedRelay
        msg.requestedAction = self.requestedAction
        msg.futureGroup = self.future_group
        msg.futureGroupName = self.future_group_name
        msg.commands = self.commands
        msg_bytes = msg.to_bytes()
        self.group_pub.send(msg_bytes)

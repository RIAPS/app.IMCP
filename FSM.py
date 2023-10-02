# riaps:keep_import:begin
import time
import applibs.helper as helper

from imcp_fsm.baseRiapsComponents.IMCP_FSM import IMCP_FSM
import utils.TerminalColors as TerminalColors

from applibs.log_preprocessor import log_json

debugMode = helper.debugMode
msgcounterLimit = helper.msgcounterLimit


# riaps:keep_import:end
class FSM(IMCP_FSM):

    # riaps:keep_constr:begin
    def __init__(self, config, topology_config):
        super(FSM, self).__init__(config=config, topology_config=topology_config)

        # Variables for group message
        self.group = []
        self.groupToSend = []
        self.requestedRelay = 'NONE'
        self.requestedAction = 'NONE'
        self.commands = []
        self.display_counter_Q = 0

        self.logger.info("Starting")

        # self.logger.info("before")
        # util_tester.setup_test_logger(self, "logfile")
        # self.logger.info("after")

    # riaps:keep_constr:end

    # riaps:keep_poller:begin
    def on_poller(self):
        now = self.poller.recv_pyobj()

        self.logger.info(f"{TerminalColors.Red}"
                         f"sending current state: {self.model.state}"
                         f"{TerminalColors.RESET}")

        self.publish_state()

    # riaps:keep_trigger:end

    # riaps:keep_group_sub:begin
    def on_group_sub(self):
        is_leader = super(FSM, self).on_group_sub()
        if not is_leader:
            return

    # riaps:keep_group_sub:end

    # riaps:keep_relay_sub:begin
    def on_relay_sub(self):
        super(FSM, self).on_relay_sub()

    # riaps:keep_event_sub:end

    # riaps:keep_timeout:begin
    def on_Timeout(self):
        super(FSM, self).on_Timeout()

    # riaps:keep_timeout:end

    # riaps:keep_impl:begin
    def convert_relay_msg_to_trigger(self, relay_id, connected, unplanned):

        if self.debugMode:
            log_json(self.logger, "info", "convert_relay_msg_to_trigger conditions",
                     event={"CONDITIONS": {"relay_id": relay_id,
                                           "connected": connected,
                                           "pcc_relay": self.pcc_relay_id,
                                           "relay_under_control": self.relayUnderControl,
                                           "action_under_control": self.actionUnderControl,
                                           "model_state": self.model.state,
                                           "unplanned": unplanned}})

        if "ACTIVE_" not in self.model.state:
            return None, False

        if unplanned:
            if relay_id == self.pcc_relay_id:
                return ('unplannedIsland', False) if not connected else ('unplannedResync', False)
            elif relay_id != self.pcc_relay_id:
                return ('unplannedDisconnect', False) if not connected else ('unplannedConnect', False)
            
        if relay_id != self.relayUnderControl:
            return None, False
        
        if relay_id == self.pcc_relay_id:
            if connected and self.model.state == 'ACTIVE_GRID-TIED':
                return None, False
            if (not connected) and self.model.state == 'ACTIVE_ISLANDED':
                return None, False

        if relay_id == self.pcc_relay_id:
            if self.model.state == 'ACTIVE_PREPARE-ISLAND':
                return ('completePlannedIsland', True) if not connected else (None, False)
            elif self.model.state == 'ACTIVE_PREPARE-RESYNC':
                return ('completeResync', True) if connected else (None, False)
            elif self.model.state in ["ACTIVE_PREPARE-CONNECT", "ACTIVE_PREPARE-DISCONNECT"]:
                return None, False  # Ignore message from PCC relay in these states.

        elif relay_id != self.pcc_relay_id:
            if self.model.state == 'ACTIVE_PREPARE-CONNECT':
                return ('completeConnect', True) if connected else (None, False)
            elif self.model.state == 'ACTIVE_PREPARE-DISCONNECT':
                return ('completeDisconnect', True) if not connected else (None, False)
            else:
                return None, False  # Ignore message from non pcc relay if we're not in a transition state.


        log_json(self.logger, "error", "Unexpected conditions",
                 event={"UNEXPECTED CONDITIONS": {"relay_id": relay_id,
                                                  "connected": connected,
                                                  "pcc_relay": self.pcc_relay_id,
                                                  "relay_under_control": self.relayUnderControl,
                                                  "action_under_control": self.actionUnderControl,
                                                  "model_state": self.model.state}})

        assert False, "Unexpected conditions, how did we get here? Was it a bug?"

    def convert_requested_action_to_trigger(self, msg):

        commandStartStop, commandPOIRelay, \
            commandEnableActiveControl, secondaryAngleCtrl_opal, \
            regulationSignal, regulationSignal2 = list(msg.commands)

        requestedRelayID = msg.requestedRelay
        requestedAction = msg.requestedAction
        groupChange = (set(msg.group) != set(msg.futureGroup))
        requestedRelayStatus = self.get_relay_status(requestedRelayID)

        if self.debugMode:
            self.logger.info(f"{TerminalColors.Orange}\n"
                             f"FSM.py - on_group_sub - convert_requested_action_to_trigger\n"
                             f"self.pcc_relay_id: {self.pcc_relay_id}\n"
                             f"requestedRelayID: {requestedRelayID}\n"
                             f"groupChange: {groupChange}\n"
                             f"requestedAction: {requestedAction}\n"
                             f"requestedRelayStatus: {requestedRelayStatus}\n"
                             f"self.model.state: {self.model.state}"
                             f"{TerminalColors.RESET}")

        # first evaluate the start/stop command
        if commandStartStop == 0 and self.model.state != 'SHUTDOWN':
            return "commandDERStop", False
        elif commandStartStop == 1 and self.model.state == 'SHUTDOWN':
            return "commandDERStart", False
        elif self.model.state == "SHUTDOWN" and commandStartStop == 0:
            return None, False  # These are the predicates for the LOCAL-CONTROL state, so don't do anything.

        # second evaluate the local/active control command
        if commandEnableActiveControl == 0 and self.model.state[0:7] == 'ACTIVE_':  # only disable it when it is active
            return "commandActiveControlDisable", False
        elif commandEnableActiveControl == 1 and self.model.state == 'LOCAL-CONTROL':
            return "commandActiveControlEnable", False
            # The transition to ACTIVE control from LOCAL-CONTROL is not coordinated
            # because LOCAL-CONTROL is not a state where coordination is available.
        elif self.model.state == "LOCAL-CONTROL" and commandEnableActiveControl == 0:
            return None, False  # These are the predicates for the LOCAL-CONTROL state, so don't do anything.

        # ---- evaluate the active control commands ---- #
        # GRID Operations
        if requestedRelayStatus == "Unknown":
            return None, False

        connected = requestedRelayStatus["connected"]

        if requestedRelayID == self.pcc_relay_id:
            # planned islanding
            if connected and self.model.state == 'ACTIVE_GRID-TIED':
                return ('requestIsland', True) if requestedAction == 'OPEN' else (None, False)
            # reconnecting
            elif (not connected) and self.model.state == 'ACTIVE_ISLANDED':
                return ('requestResync', True) if requestedAction == 'CLOSE' else (None, False)
            elif "PREPARE" in self.model.state:
                return None, False  # This is a waiting state, so don't do anything

        # Feeder Operations
        elif requestedRelayID != self.pcc_relay_id:
            if not groupChange:
                return None, False
            elif "PREPARE" in self.model.state:
                return None, False # This is a waiting state, so don't do anything
            # disconnecting adjacent feeder in islanded mode
            elif connected and self.model.state == "ACTIVE_ISLANDED":
                return ('requestDisconnect', True) if requestedAction == 'OPEN' else (None, False)
            # connecting adjacent feeder in islanded mode.
            # see https://github.com/RIAPS/app.MgManage/blob/new-fsm-integration/FSM.py#L196
            elif (not connected) and self.model.state == "ACTIVE_ISLANDED":
                return ('requestConnect', True) if requestedAction == 'CLOSE' else (None, False)
            else:
                # TODO: What if I'm in a state other than ACTIVE_ISLANDED and I get a request to connect/disconnect a
                #  non-PCC relay?
                #  For now let's write a log stating it is not supported and return None. This was not supported in the original app either. 
                log_json(self.logger, "warn",
                         "Unsupported request to connect/disconnect a non-PCC relay while not ISLANDED",
                         event={"UNSUPPORTED REQUEST": {"commandStartStop": commandStartStop,
                                                        "model_state": self.model.state,
                                                        "commandEnableActiveControl": commandEnableActiveControl,
                                                        "requestedRelayID": requestedRelayID,
                                                        "pcc_relay": self.pcc_relay_id,
                                                        "requestedAction": requestedAction,
                                                        "connected": connected,
                                                        "groupChange": groupChange}})
                return None, False  
                

        log_json(self.logger, "error", "Unexpected conditions",
                 event={"UNEXPECTED CONDITIONS": {"commandStartStop": commandStartStop,
                                                  "model_state": self.model.state,
                                                  "commandEnableActiveControl": commandEnableActiveControl,
                                                  "requestedRelayID": requestedRelayID,
                                                  "pcc_relay": self.pcc_relay_id,
                                                  "requestedAction": requestedAction,
                                                  "connected": connected,
                                                  "groupChange": groupChange}})

        assert False, "Unexpected conditions, how did we get here? Was it a bug?"

    def update_dc_group(self, instance_name: str, group_members: list):

        self.logger.info(f"{TerminalColors.Red}\n"
                         f"FSM.py - update_dc_group \n"
                         f"instance name: {instance_name} | members: {str(group_members)}"
                         f"{TerminalColors.RESET}")

        if self.dcgroup:
            # If the distributed coordination group is the same as the group instance name then there is no need to
            # change groups, so return.
            if self.dcgroup.groupInstance == instance_name:
                self.logger.info(f"{TerminalColors.White}\n"
                                 f"FSM.py - update_dc_group | No change to group membership "
                                 f"instance name: {instance_name} | members: {group_members}"
                                 f"{TerminalColors.RESET}")
                return
            else:
                self.logger.info(f"{TerminalColors.White}\n"
                                 f"FSM.py - update_dc_group \n"
                                 f"Change group from {self.dcgroup.groupInstance} "
                                 f"to {instance_name} "
                                 f"{TerminalColors.RESET}")
                self.leaveGroup(self.dcgroup)
        else:
            self.logger.info(f"{TerminalColors.White}\n"
                             f"FSM.py - update_dc_group \n"
                             f"No group, join {instance_name}"
                             f"{TerminalColors.RESET}")
        self.dcgroup = self.joinGroup(groupName="Microgrid", instName=instance_name)
        log_json(self.logger, "info", "Joined group",
                 event=f"JOINED_GROUP: {self.dcgroup.groupInstance},"
                       f"groupSize: {self.dcgroup.groupSize}")

    def handleActionVoteRequest(self, group, rfcId, when):
        vote_msg = group.recv_pyobj()
        trigger = vote_msg["trigger"]
        vote = getattr(self.model, f"may_{trigger}")()
        self.logger.info(f'handleActionVoteRequest[{str(rfcId)}] = '
                         f'{str(trigger)} @ {str(when)} -->  {str(vote)}')
        self.rfcids[rfcId] = vote_msg
        group.sendVote(rfcId, vote)

    def handleVoteResult(self, group, rfcId, vote):
        """
         Handle consensus vote result (yes/no/timeout)
         Note: This is a riaps function
        """
        # assert (group == self.group)
        self.logger.info(f'vote_id: {rfcId} | handleVoteResult = {str(vote)} '
                         f'group that is voting: {group} and type: {type(group)} '
                         f'dcgroup groupSize: {self.dcgroup.groupSize}')
        # I guess dcgroup is a thread because I can't seem to call the Group class's groupSize() method.

        vote_msg = self.rfcids.get(rfcId)

        if not vote_msg:
            log_json(self.logger, "warn", "We missed the vote request for {vote}, but got the result",
                     event="MISSED VOTE. GOT RESULT")
            # TODO: This could happen if there is a majority vote. How should this be handled?
            #  Go to local control and rejoin?
            # On a related note, if we notice we are in a state different from other group members what should we do?
            return

        if vote == "timeout":
            self.logger.info(f"{str(rfcId)} Poll expired before {vote_msg['kind']} was reached")
            return
        
        if vote == "no":
            self.logger.info(f"{str(rfcId)} {vote_msg['kind']} was not reached")
            return

        if vote != "yes":
            self.logger.info(f"{str(rfcId)} Somehow got a weird value for vote: {vote}")
            return

        # vote == "yes"

        # lock the relay if the transition is to happen
        self.relayUnderControl = vote_msg['requestRelay']
        self.actionUnderControl = vote_msg['requestAction']
        # make the transition
        self.model.trigger(vote_msg["trigger"],
                           coordinated="True",
                           info=f"Vote: {vote}, "
                                f"kind: {vote_msg['kind']}, "
                                f"rfcID: {str(rfcId)}")

        now = time.time()
        latency = now - vote_msg["cmd_timestamp"]
        self.logger.info(f"{str(rfcId)} COMMAND LATENCY: {latency}")
        self.logger.info(f"{str(rfcId)} CONSENSUS LATENCY: {now - vote_msg['vote_start']}")
        self.logger.info(f"{str(rfcId)} relay and action: {self.relayUnderControl}:{self.actionUnderControl}")

        self.publish_state(cause="handleVoteResult")

    def handleActivate(self):
        super(FSM, self).handleActivate()
        log_json(self.logger,
                 "info",
                 f"model.state: {self.model.state}",
                 event=f"ENTER STATE: {self.model.state}")

    def handlePeerStateChange(self, state, uuid):
        super(FSM, self).handlePeerStateChange(state, uuid)

# riaps:keep_impl:end

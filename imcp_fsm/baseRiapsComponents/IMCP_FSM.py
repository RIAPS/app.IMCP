# riaps:keep_import:begin
import abc
import time
import yaml

import imcp_capnp
from riaps.run.comp import Component

from imcp_fsm.machines import riaps as machine
from imcp_fsm import model
import utils.TerminalColors as TerminalColors

from applibs.log_preprocessor import log_json


# riaps:keep_import:end
class IMCP_FSM(Component):

    # riaps:keep_constr:begin
    # def __init__(self, uuid, testlog):
    def __init__(self, config, topology_config):
        with open(config, "r") as f:
            cfg = yaml.safe_load(f)
        with open(topology_config, "r") as f:
            group_config = yaml.safe_load(f)
        super(IMCP_FSM, self).__init__()
        self.logger.info(f"{TerminalColors.Green} IMCP_FSM.py - init {TerminalColors.RESET}")
        self.debugMode = cfg.get("debugMode", False)
        self.uuid = cfg["uuid"]

        # Variables used to store fsm
        self.machine = None
        self.model = None
        self.inital_state = cfg["initial_state"]

        # Setting relayUnderControl to a single value is ok as long as the operator
        # is not controlling multiple relays at once.
        self.relayUnderControl = None
        self.actionUnderControl = None
        self.pcc_relay_id = cfg["Feeder"]
        self.relays_status = {}

        # Variable used for messaging timeouts
        self.msg_timeouts = cfg["msg_timeouts"]
        self.time_of_last_group_msg = None
        self.time_of_last_relay_msg = None
        self.vote_timeout = cfg["vote_timeout"]

        # Variable used to track when last state message was sent by FSM.
        self.time_of_last_state_msg = time.time()
        self.MAX_STATE_PUBLISH_DELAY_SECONDS = cfg["MAX_STATE_PUBLISH_DELAY_SECONDS"]

        # Variables used for group consensus
        self.rfcids = {}  # request for consensus
        self.kind = "consensus"  # kind" is "consensus" or "majority"
        self.dcgroup = ""

    # riaps:keep_constr:end

    # riaps:keep_timeout:begin
    def on_state_timer(self):

        now = self.state_timer.recv_pyobj()  # Receive time

        #  This is to avoid calling the state timeout functions for states that have already been exited.
        #  If the time on this message is before the time when the previous state was exited then it is
        #  no longer relevant.
        if now < machine.global_state_log["prior"]["timestamp"]:
            self.logger.info(f"TIMEOUT at {now} "
                             f"was canceled "
                             f"{machine.global_state_log['prior']['timestamp'] - now} "
                             f"seconds before the timeout fired")
            return

        state = self.machine.get_state(self.model.state)

        #  If the state has a timeout, process the timeout callbacks.
        if state.timeout > 0:
            event_data = state.runner[id(self.model)]["event_data"]
            current = machine.global_state_log['current']
            prior = machine.global_state_log['prior']
            self.logger.info(f"{TerminalColors.Green}\n"
                             f"IMCP_FSM.py - on_state_timer\n"
                             f"STATE TIMEOUT at {now} \n"
                             f"Exited prior state: {prior['state']} at {prior['timestamp']} \n"
                             f"Entered current state: {current['state']} at {current['timestamp']} \n"
                             f"Processing callbacks..."
                             f"{TerminalColors.RESET}")

            for callback in state.on_timeout:
                self.logger.debug(f"Processing callback: {callback}")
                event_data.machine.callback(callback, event_data)
            self.logger.debug(f"TIMEOUT callbacks processed for {state.name}")

    # riaps:keep_timeout:end

    # riaps:keep_msg_timeout:begin
    def on_msg_timer(self):
        now = self.msg_timer.recv_pyobj()  # Receive time

        if not self.msg_timeouts["next"]:
            return

        for source, value in self.msg_timeouts["time"].items():
            # value < now + 0.05 means that if the timer is going to expire within the next
            # 50 milliseconds, then treat it as if it has already expired.
            # This is to avoid setting a timer for less than 50 milliseconds.
            # TODO: The timeout buffer should be moved to the config file.
            if value < now + 0.05:
                time_of_last_msg = getattr(self, f"time_of_last_{source}_msg")
                time_since_last_msg = now - time_of_last_msg
                self.logger.info(f"{TerminalColors.Green}\n"
                                 f"IMCP_FSM.py - on_msg_timer \n"
                                 f"MISSING {source} MESSAGES. \n"
                                 f"Last {source} msg was at: {self.time_of_last_group_msg} \n"
                                 f"Current time is: {now} \n"
                                 f"time since last {source} msg: {time_since_last_msg}"
                                 f"{TerminalColors.RESET}")
                self.msg_timeouts["time"][source] = now + self.msg_timeouts["delay"][source]

        self.trigger(event="missingMessages", publish_reason="on_msg_timer")
        self.set_next_timer()

    # riaps:keep_msg_timeout:end

    # riaps:keep_group_sub:begin
    def on_group_sub(self):

        # --- Reset group timer ---
        self.time_of_last_group_msg = time.time()
        self.msg_timeouts["time"]["group"] = time.time() + self.msg_timeouts["delay"]["group"]
        if self.msg_timeouts["next"] == "group":
            self.msg_timer.cancel()
            self.set_next_timer()

        # --- Fetch the message --
        msg_bytes = self.group_sub.recv()
        msg = imcp_capnp.GroupMsg.from_bytes(msg_bytes)

        # --- Begin msg contents ---
        msg_device_name = msg.sender
        msg_time = msg.timestamp
        msg_counter = msg.msgcounter
        self.group = list(msg.group)
        instance_name = msg.groupName
        self.requestedRelay = msg.requestedRelay
        self.requestedAction = msg.requestedAction
        when = msg.timestamp  # msg.requestedTime
        self.futureGroup = list(msg.futureGroup)
        commands = list(msg.commands)

        log_json(self.logger, "info", "received group message",
                 event={"GROUP_MSG": msg.to_dict(),
                        "model state": self.model.state if self.model else None,
                        "pcc_relays_status": self.relays_status.get(self.pcc_relay_id, False),
                        "requested_relay": f"{self.requestedRelay} type: {type(self.requestedRelay)} compare: {self.requestedRelay == 'NONE'}",
                        "requested_action": self.requestedAction,
                        "relays_status": self.relays_status.get(self.requestedRelay, False)})
        # --- End msg contents ---

        # Check Preconditions
        if not self.model:
            log_json(self.logger, level="error", message="How did we get here with an undefined model?",
                     event="UNEXPECTED LACK OF MODEL DEFINITION")
            return False  # TODO: This should be removed eventually.
        if not self.relays_status.get(self.pcc_relay_id):
            return False  # No relay status for the PCC relay yet, so no need to process the message.
        if not commands:
            return False  # The operator has not specified the desired state yet.
        if not instance_name:
            return False  # If there is no instance_name the group manager hasn't run group management yet so skip.
        
        # Do work
        if self.requestedRelay != 'NONE':
            # If the requested state (OPEN/CLOSE) is different from the current state then a transition is required.
            relay_state = self.relays_status[self.requestedRelay]["relay_state"]
            if relay_state and relay_state != self.requestedAction:
                self.relays_status[self.requestedRelay]["requested_state"] = self.requestedAction
                self.relays_status[self.requestedRelay]["transition_required"] = True

        self.update_dc_group(instance_name=instance_name, group_members=self.group)
        # Update cyber connection based on physical connection as determined by the group manager.

        trigger, coordinated = self.convert_requested_action_to_trigger(msg)

        if self.debugMode:
            self.logger.info(f"{TerminalColors.Green}\n"
                             f"IMCP_FSM.py - on_group_sub | convert_requested_action_to_trigger | "
                             f"trigger: {trigger}, coordinated: {coordinated}"
                             f"{TerminalColors.RESET}")

        if not trigger:
            return
        if not coordinated:
            relay_status = self.get_relay_status(self.pcc_relay_id)
            self.model.trigger(trigger, relay_status=relay_status)
            self.publish_state(cause="on_group_sub")  # TODO: When should I actually publish state updates?
            return

        # Otherwise start a vote for a coordinated transition:
        # Assumption is that the operator periodically sends the message for the desired state.
        # So, there is no need to check if there is a leader since this port will be called again.
        if not self.dcgroup:
            self.logger.debug(f"IMCP_FSM.py - on_group_sub | Not in a group")
            return
        if not self.dcgroup.isLeader():
            self.logger.info(f"IMCP_FSM.py - on_group_sub | I'm not the leader")
            return False

        self.logger.info(f"IMCP_FSM.py - on_group_sub | I'm the leader")
        # This node is the leader so build and send a vote request.

        vote_msg = {
            "trigger": trigger,
            "cmd_timestamp": msg_time,
            "kind": self.kind,
            "vote_start": time.time(),
            "requestRelay": msg.requestedRelay,
            "requestAction": msg.requestedAction
        }

        self.logger.info(f"{TerminalColors.White}\n"
                         f"IMCP_FSM.py - on_group_sub | send vote request: {vote_msg}"
                         f"{TerminalColors.RESET}")

        # The default value for "kind" appears to be "consensus", specified in riaps/lang/riaps.tx
        rfv_id = self.dcgroup.requestActionVote_pyobj(vote_msg,
                                                      when,
                                                      kind=self.kind,
                                                      timeout=self.vote_timeout)

        log_json(self.logger, "info", "sent request for vote",
                 event={"REQUESTED_ACTION_VOTE": trigger,
                        "rfvId": rfv_id})

    # riaps:keep_group_sub:end

    # riaps:keep_relay_sub:begin
    def on_relay_sub(self):

        # --- Reset relay timer ---
        self.time_of_last_relay_msg = time.time()
        self.msg_timeouts["time"]["relay"] = time.time() + self.msg_timeouts["delay"]["relay"]
        if self.msg_timeouts["next"] == "relay":
            self.msg_timer.cancel()
            self.set_next_timer()

        # --- Fetch the message --
        msg_bytes = self.relay_sub.recv()
        msg = imcp_capnp.RelayMsg.from_bytes(msg_bytes)
        msg_dict = msg.to_dict()

        # --- Begin msg contents ---
        relay_id = msg.sender
        connected = msg_dict["connected"]

        # To detect whether the change was unplanned or not
        # we track compare the current and target states,
        # as well as whether we reached the target state since the
        # last change to the target.
        relay_state = "CLOSE" if connected else "OPEN"
        if not self.relays_status.get(relay_id):
            self.relays_status[relay_id] = {}
        self.relays_status[relay_id]["connected"] = connected
        self.relays_status[relay_id]["relay_state"] = relay_state

        requested_state = self.relays_status[relay_id].get("requested_state")
        # May not have been set by a group message yet.
        unplanned = False
        if requested_state:
            # If the relay state is the same as the requested state then no transition is required.
            if relay_state == requested_state:
                self.relays_status[relay_id]["transition_required"] = False
            # Otherwise, the state is different from the requested state and if no transition is required
            # then the change was unplanned.
            else:
                if self.relays_status[relay_id].get("transition_required") is False:
                    unplanned = True

        trigger, coordinated = self.convert_relay_msg_to_trigger(relay_id, connected, unplanned)
        if self.debugMode:
            self.logger.info(f"{TerminalColors.Green}"
                             f"IMCP_FSM.py - on_relay_sub | convert_relay_msg_to_trigger | "
                             f"trigger: {trigger}, coordinated: {coordinated}"
                             f"{TerminalColors.RESET}")

        if not trigger:
            self.publish_state(cause="on_relay_sub")
            return True

        if not coordinated:
            self.model.trigger(trigger)
            self.publish_state(cause="on_relay_sub")
            return True

        # Otherwise start a vote for a coordinated transition:
        if not self.dcgroup:
            self.logger.debug(f"IMCP_FSM.py - on_relay_sub | Not in a group")
            return
        if not self.dcgroup.isLeader():
            self.logger.info(f"IMCP_FSM.py - on_relay_sub | I'm not the leader")
            return False

        self.logger.info(f"IMCP_FSM.py - on_relay_sub | I'm the leader")
        # This node is the leader so build and send a vote request.
        vote_msg = {
            "trigger": trigger,
            "cmd_timestamp": time.time(),
            "kind": self.kind,
            "vote_start": time.time(),
            "requestRelay": relay_id,
            "requestAction": relay_state
        }

        self.logger.info(f"{TerminalColors.White}\n"
                         f"IMCP_FSM.py - on_relay_sub | send vote request: {vote_msg}"
                         f"{TerminalColors.RESET}")

        # The default value for "kind" appears to be "consensus", specified in riaps/lang/riaps.tx
        rfv_id = self.dcgroup.requestActionVote_pyobj(vote_msg,
                                                      time.time(),
                                                      kind=self.kind,
                                                      timeout=self.vote_timeout)

        log_json(self.logger, "info", "sent request for vote",
                 event={"REQUESTED_ACTION_VOTE": trigger,
                        "rfvId": rfv_id})

    # riaps:keep_event_sub:end

    # riaps:keep_impl:

    def get_relay_status(self, relay_id):
        return self.relays_status.get(relay_id, "Unknown")

    def publish_state(self, cause):

        now = time.time()
        max_publish_delay_exceeded = False
        if now >= self.time_of_last_state_msg + self.MAX_STATE_PUBLISH_DELAY_SECONDS:
            max_publish_delay_exceeded = True
            self.time_of_last_state_msg = now

        if not cause and not max_publish_delay_exceeded:
            return

        if self.model.state == 'ACTIVE_PREPARE-DISCONNECT':
            groupToSend = self.futureGroup  # future group for power sharing when disconnect
        else:
            groupToSend = self.group

        msg = imcp_capnp.StateMsg.new_message()
        msg.sender = self.uuid
        msg.timestamp = time.time()
        msg.msgcounter = 0
        msg.currentState = self.model.state
        if self.relayUnderControl:
            msg.breaker = self.relayUnderControl
            msg.action = self.actionUnderControl
        else:
            msg.breaker = 'NONE'
            msg.action = 'NONE'
        msg.group = groupToSend
        msg.reconfigcontrol = False
        msg_bytes = msg.to_bytes()

        self.logger.info(f"{TerminalColors.Red}\n"
                         f"IMCP_FSM.py - publish_state | cause: {cause}\n"
                         f"msg: {msg}"
                         f"{TerminalColors.RESET}")
        self.state_pub.send(msg_bytes)

    def trigger(self, event, relay_status=None, publish_reason=None):
        self.model.trigger(event, relay_status=relay_status)
        self.publish_state(cause=publish_reason)
        log_json(self.logger, "info", "trigger", event)

    @abc.abstractmethod
    def update_dc_group(self, instance_name, group_members):
        pass

    @abc.abstractmethod
    def compute_relay_status(self, msg_dict):
        pass

    @abc.abstractmethod
    def convert_relay_msg_to_trigger(self, relay_id, status, unplanned):
        pass

    @abc.abstractmethod
    def convert_requested_action_to_trigger(self, msg):
        pass

    def set_next_timer(self):
        timeouts = self.msg_timeouts["time"]
        next_timeout = min(timeouts, key=timeouts.get)
        self.msg_timeouts["next"] = next_timeout
        next_delay = timeouts[next_timeout] - time.time()
        if next_delay < 0:
            next_delay = 0
            # It is possible that the timer expired while this function was running so trigger the timeout asap.
        self.msg_timer.setDelay(float(next_delay))
        self.msg_timer.launch()

    def handleActivate(self):

        extra_args = dict(auto_transitions=False,
                          initial=self.inital_state,
                          # initial='ACTIVE_GRID-TIED',
                          # title='DYNAMIC MG FSM',
                          # show_conditions=True,
                          # show_state_attributes=True,
                          ignore_invalid_triggers=True)

        self.model = model.ICMPModel(self.state_timer)
        self.machine = machine.RIAPSStateMachine(model=self.model,
                                                 states=model.states,
                                                 transitions=model.transitions,
                                                 before_state_change="before_state_change",
                                                 after_state_change="after_state_change",
                                                 send_event=True,
                                                 **extra_args)

        now = time.time()
        self.time_of_last_group_msg = now
        self.time_of_last_relay_msg = now
        self.msg_timeouts["time"]["relay"] = now + self.msg_timeouts["delay"]["relay"]
        self.msg_timeouts["time"]["group"] = now + self.msg_timeouts["delay"]["group"]
        self.set_next_timer()

    def handlePeerStateChange(self, state, uuid):
        pass

    def handleGroupMessage(self, _group):
        pass

    def handleMemberJoined(self, group, memberId):
        pass

    def handleMemberLeft(self, group, memberId):
        pass

    def __destroy__(self):
        self.logger.info('Stopping...')
        self.logger.flush()

        # riaps:keep_impl:end

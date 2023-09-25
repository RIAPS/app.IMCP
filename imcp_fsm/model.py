import io
import logging
import spdlog
import time
import yaml

from riaps.utils import spdlog_setup

from imcp_fsm.definitions import ROOT_DIR
import utils.TerminalColors as TerminalColors
from applibs.log_preprocessor import log_json


with open(f"{ROOT_DIR}/states.yaml", "r") as file:
    state_defs = yaml.safe_load(file)
with open(f"{ROOT_DIR}/transitions.yaml") as file:
    transition_defs = yaml.safe_load(file)

states = state_defs["top_states"]
states.append({"name": "ACTIVE",
               "children": state_defs["active_states"],
               "transitions": transition_defs["active_transitions"]})

transitions = transition_defs["transitions"]


def add_feature(name, feature):
    for state in state_defs["active_states"]:
        state[name] = feature

    for state in state_defs["top_states"]:
        state[name] = feature


def add_timeout(timeout):
    for state in state_defs["active_states"]:
        if "timeout" in state:
            state["riaps_timer"] = timeout

    for state in state_defs["top_states"]:
        if "timeout" in state:
            state["riaps_timer"] = timeout


class ICMPModel(object):
    def __init__(self, timeout):

        spdlog_setup.from_file("riaps-log.conf")

        self.logger = spdlog_setup.get_logger(__name__)
        if not self.logger:
            self.logger = spdlog_setup.get_logger("imcp")
            self.logger.info(f"Add {__name__} to loggers. \n Available loggers: {spdlog_setup.loggers}")

        add_timeout(timeout)
        add_feature("logger", self.logger)

        self.Prep4Island_CNTR = 0
        self.Prep4Grid_CNTR = 0
        self.Prep4Disconnect_CNTR = 0
        self.Prep4Connect_CNTR = 0
        self.is_connected = True

        super(ICMPModel, self).__init__()

    def before_state_change(self, event_data):
        coordinated = "False"
        if "coordinated" in event_data.kwargs:
            info = event_data.kwargs["info"]
            coordinated = f"True; {info}"

        self.logger.info(f"EXIT STATE: {self.state} "
                         f"TRIGGER: {event_data.event.name} "
                         f"TIME: {time.time()} "
                         f"COORDINATED: {coordinated}")

    def after_state_change(self, event_data):
        coordinated = "False"
        if "coordinated" in event_data.kwargs:
            info = event_data.kwargs["info"]
            coordinated = f"True {info}"
        self.logger.info(f"{TerminalColors.Orange}"
                         f"ENTER STATE: {self.state} "                         
                         f"TRIGGER: {event_data.event.name} "
                         f"TIME: {time.time()} "
                         f"COORDINATED: {coordinated}"
                         f"{TerminalColors.RESET}")

    # on_enter
    def IncPrep4Island_CNTR(self, event_data):
        self.Prep4Island_CNTR += 1
        if self.Prep4Island_CNTR >= 2:
            self.logger.info(f"attempt {self.Prep4Island_CNTR} give up on island")
            log_json(self.logger, "info", f"attempt {self.Prep4Island_CNTR} give up on island",
                     event={"FAIL": "ISLAND"})
            self.Prep4Island_CNTR = 0
            self.failIsland()
        else:
            self.logger.info(f"attempt {self.Prep4Island_CNTR} try to disconnect again")
            self.retryIsland()

    # on_enter
    def IncPrep4Grid_CNTR(self, event_data):
        self.Prep4Grid_CNTR += 1
        if self.Prep4Grid_CNTR >= 2:
            self.logger.info(f"attempt {self.Prep4Grid_CNTR} give up on connect")
            log_json(self.logger, "info", f"attempt {self.Prep4Grid_CNTR} give up on resync",
                     event={"FAIL": "RESYNC"})
            self.Prep4Grid_CNTR = 0
            self.failResync()
        else:
            self.logger.info(f"attempt {self.Prep4Grid_CNTR} try to connect again")
            self.retryResync()

    def IncPrep4Disconnect_CNTR(self, event_data):
        self.Prep4Disconnect_CNTR += 1
        if self.Prep4Disconnect_CNTR >= 2:
            self.logger.info(f"attempt {self.Prep4Disconnect_CNTR} give up on disconnect {event_data.kwargs}")
            log_json(self.logger, "info", f"attempt {self.Prep4Disconnect_CNTR} give up on disconnect",
                     event={"FAIL": "DISCONNECT", "kwargs": event_data.kwargs})
            self.Prep4Disconnect_CNTR = 0
            self.failDisconnect()
        else:
            self.logger.info(f"attempt {self.Prep4Grid_CNTR} try to connect again")
            self.retryDisconnect()

    def IncPrep4Connect_CNTR(self, event_data):
        self.Prep4Connect_CNTR += 1
        if self.Prep4Connect_CNTR >= 2:
            self.logger.info(f"attempt {self.Prep4Connect_CNTR} give up on connect")
            log_json(self.logger, "info", f"attempt {self.Prep4Connect_CNTR} give up on connect",
                     event={"FAIL": "CONNECT", "kwargs": event_data.kwargs})
            self.Prep4Connect_CNTR = 0
            self.failConnect()
        else:
            self.logger.info(f"attempt {self.Prep4Connect_CNTR} try to connect again")
            self.retryConnect()

    # condition
    def connected(self, event_data):
        return self.is_connected

    # on_enter
    def placeholderOnEnter(self, event_data):
        # reset counters
        self.Prep4Island_CNTR = 0
        self.Prep4Grid_CNTR = 0
        self.Prep4Disconnect_CNTR = 0
        self.Prep4Connect_CNTR = 0

    # on_enter
    def disconnect(self, event_data):
        self.is_connected = False

    # on_enter
    def connect(self, event_data):
        self.is_connected = True

    # unless
    def InstabilityDetect(self, event_data):
        InstabilityDetected = False
        self.logger.info(f"Grid is {'unstable' if InstabilityDetected else 'stable'}")
        if InstabilityDetected:
            return True
        else:
            return False

    # condition
    def PCC_VoltFreqNorm(self, event_data):
        return True

    def gridDetected(self, event_data):
        if "relay_status" in event_data.kwargs:
            relay_status = event_data.kwargs["relay_status"]
            is_connected = relay_status["connected"]
            # is_synchronized = relay_status["synchronized"]
            # has_zeroPowerFlow = relay_status["zeroPowerFlow"]

            return is_connected




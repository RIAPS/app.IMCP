import logging
import spdlog
import time

import transitions
from transitions.core import listify
from transitions.extensions.nesting import NestedState
from transitions.extensions.states import Tags
from transitions.extensions.nesting import HierarchicalMachine as Machine
# from libs.transitions.transitions.extensions.diagrams import HierarchicalGraphMachine as Machine

import utils.TerminalColors as TerminalColors

from applibs.log_preprocessor import log_json

logging.basicConfig()
_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())

global_state_log = {"prior": {"state": None,
                              "timestamp": 0.0}}


class RIAPSState(Tags, NestedState):
    """ Adds timeout functionality to a state. Timeouts are handled model-specific.
       Attributes:
           timeout (float): Seconds after which a timeout function should be called.
           on_timeout (list): Functions to call when a timeout is triggered.
       """
    dynamic_methods = ['on_timeout']

    def __init__(self, *args, **kwargs):
        """
        Args:
            **kwargs: If kwargs contain 'timeout', assign the float value to self.timeout.
            If timeout is set, 'on_timeout' needs to be passed with kwargs as well or an AttributeError will
            be thrown.
            If timeout is not passed or equal 0 then it will not be used. It is simply
            assigned a value here so that it is not None.
            This is a reimplementation of the pytransitions states.py to use a riaps timer.:
            https://github.com/pytransitions/transitions/blob/master/transitions/extensions/states.py
        """

        provided_logger = kwargs.pop("logger")
        logger = provided_logger
        if not provided_logger:
            try:
                existing_logger = spdlog.get(name=__name__)
                logger = existing_logger
                logger.info(f"No logger provided")
            except Exception as e:
                new_logger = spdlog.ConsoleLogger(name=__name__,
                                                  multithreaded=True,
                                                  stdout=True,
                                                  colored=False)
                logger = new_logger
                logger.info(f"Created new logger")

        self.logger = logger

        self.riaps_timer = kwargs.pop("riaps_timer", None)

        self.timeout = kwargs.pop('timeout', 0)
        self._on_timeout = None

        if self.timeout > 0:
            try:
                self.on_timeout = kwargs.pop('on_timeout')
            except KeyError:
                raise AttributeError("Timeout state requires 'on_timeout' when timeout is set.")  # from KeyError
        else:
            self._on_timeout = kwargs.pop('on_timeout', [])
        self.runner = {}
        super(RIAPSState, self).__init__(*args, **kwargs)

    def enter(self, event_data):
        """ Extends `transitions.core.State.enter` by starting a timeout timer for the current model
            when the state is entered and self.timeout is larger than 0.
        """
        self.logger.info(f"{TerminalColors.Orange}"
                         f"ENTER STATE: {self.name} Time: {time.time()}"
                         f"{TerminalColors.RESET}")
        log_json(self.logger,
                 "info",
                 f"ENTER STATE: {self.name} Time: {time.time()}",
                 event={"ENTER_STATE": self.name,
                        "trigger": event_data.event.name})

        global_state_log["current"] = {"state": self.name,
                                       "timestamp": time.time()
                                       }

        if self.timeout > 0:
            self.riaps_timer.setDelay(float(self.timeout))  # Set the sporadic timer delay
            self.riaps_timer.launch()  # Launch the sporadic timer
            self.runner[id(event_data.model)] = {"timer": self.riaps_timer,
                                                 "event_data": event_data,
                                                 "state": self.name}

        return super(RIAPSState, self).enter(event_data)

    def exit(self, event_data):
        """ Extends `transitions.core.State.exit` by canceling a timer for the current model. """
        riaps_timer = self.runner.get(id(event_data.model), None)
        if riaps_timer is not None:
            if riaps_timer["timer"].thread.is_alive():
                self.logger.info(f"stop timer")
                riaps_timer["timer"].cancel()
                global_state_log["prior"] = {"state": self.name,
                                             "timestamp": time.time()}
                self.logger.info(f"EXIT STATE: {self.name} LOG: {global_state_log} LOG ID: {id(global_state_log)}")
        return super(RIAPSState, self).exit(event_data)

    def _process_timeout(self, event_data):
        # _LOGGER.debug("%sTimeout state %s. Processing callbacks...", event_data.machine.name, self.name)
        for callback in self.on_timeout:
            event_data.machine.callback(callback, event_data)
        # self.logger.info("%sTimeout state %s processed.", event_data.machine.name, self.name)

    @property
    def on_timeout(self):
        """ List of strings and callables to be called when the state timeouts. """
        return self._on_timeout

    @on_timeout.setter
    def on_timeout(self, value):
        """ listify passed values and assigns them to on_timeout."""
        self._on_timeout = listify(value)


class RIAPSStateMachine(Machine):
    state_cls = RIAPSState

    def __init__(self, *args, **kwargs):
        assert transitions.__version__ == "0.9.0", f"Wrong version installed, " \
                                                   f"installed version is: {transitions.__version__} " \
                                                   f"need version 0.9.0"
        super(RIAPSStateMachine, self).__init__(*args, **kwargs)

import logging
import spdlog
import transitions
from transitions.extensions.nesting import NestedState
from transitions.extensions.states import Timeout, Tags
from transitions.extensions.diagrams import HierarchicalGraphMachine as Machine


class CustomState(Timeout, Tags, NestedState):
    separator = NestedState.separator

    def __init__(self, *args, **kwargs):

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
        super(CustomState, self).__init__(*args, **kwargs)


class CustomStateMachine(Machine):
    print(transitions.__version__)
    state_cls = CustomState


if __name__ == '__main__':
    states = ['A', 'B', {'name': 'C', 'children': ['1', '2', '3']}, 'D']
    transitions = [
        {'trigger': 'walk', 'source': 'A', 'dest': 'B'},
        {'trigger': 'run', 'source': 'B', 'dest': 'C'},
        {'trigger': 'run_fast', 'source': 'C', 'dest': 'C{0}1'.format(NestedState.separator)},
        {'trigger': 'sprint', 'source': 'C', 'dest': 'D'}
    ]

    m = CustomStateMachine(
        states=states,
        transitions=transitions,
        initial='A', auto_transitions=False)

    assert m.may_walk()

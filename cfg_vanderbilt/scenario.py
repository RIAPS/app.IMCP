
class Scenario:
    def __init__(self, initial_state):
        self.target_state = initial_state
        self.current_state = self.get_state_defs(initial_state)

    def next_state(self):
        next_state = self.current_state["next_state"]
        self.target_state = next_state
        self.current_state = self.get_state_defs(next_state)

    def get_state_defs(self, state_name):
        state_defs = {
            "SHUTDOWN": {
                "minimum_time_in_state": 1,
                "next_state": "LOCAL-CONTROL",
                "requestedAction": "NONE",
                "requestedRelay": "NONE",
                "signals": {
                    "StartStop": 0,
                    "GridTiedOp": 0,
                    "SecCtrlEnable": 0,
                    "SecCtrlAngleEnable": 0,
                    "RegulationSignal": 0,  # for direct PQ command
                    "RegulationSignal2": 0  # for direct PQ command
                }},
            "LOCAL-CONTROL": {
                "minimum_time_in_state": 1,
                "next_state": "ACTIVE_GRID-TIED",
                "requestedAction": "NONE",
                "requestedRelay": "NONE",
                "signals": {
                    "StartStop": 1,
                    "GridTiedOp": 0,
                    "SecCtrlEnable": 0,
                    "SecCtrlAngleEnable": 0,
                    "RegulationSignal": 0,
                    "RegulationSignal2": 0
                }},
            "ACTIVE_GRID-TIED": {
                "minimum_time_in_state": 25,
                "next_state": "ACTIVE_ISLANDED",
                "requestedAction": "CLOSE",
                "requestedRelay": "PCC",
                "signals": {
                    "StartStop": 1,
                    "GridTiedOp": 0,
                    "SecCtrlEnable": 1,
                    "SecCtrlAngleEnable": 0,
                    "RegulationSignal": 0,
                    "RegulationSignal2": 0
                }},
            "ACTIVE_ISLANDED": {
                "minimum_time_in_state": 100,
                "next_state": None,
                "requestedAction": "OPEN",
                "requestedRelay": "PCC",
                "signals": {
                    "StartStop": 1,
                    "GridTiedOp": 0,
                    "SecCtrlEnable": 1,
                    "SecCtrlAngleEnable": 0,
                    "RegulationSignal": 0,
                    "RegulationSignal2": 0
                }}
        }
        return state_defs[state_name]

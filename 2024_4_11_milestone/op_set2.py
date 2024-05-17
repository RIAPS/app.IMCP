import fabric2 as fab
import json
import math
import pathlib
import yaml
import api
import time


def set_values(device_name, config_path, pq_map):
    # Load device configuration
    path_to_file = config_path / f"{device_name}.yaml"
    assert path_to_file.is_file(), f"Config file for {device_name} not found."

    with open(path_to_file, "r") as f:
        device_config = yaml.safe_load(f)

    protocol = device_config["Protocol"]
    ip = device_config["TCP"]["Address"]

    if protocol == "TCP":
        api.set_OP(device_name, pq_map)
    elif protocol == "Serial":
        c = fab.Connection(ip)
        c.run("hostname")
        c.run(
            f"python3 ~/UC3_SET_OP_PNTS/scripts/api.py --der_name {device_name} --PQ_map '{json.dumps(pq_map)}' --fun 'set'"
        )


def main():
    COS_PHI = 0.95  # Power factor

    # Define the power factor for calculations
    def get_q(p):
        return p * math.tan(math.acos(COS_PHI))

    # Define the configurations for each step
    step_configs = [
        # {"F1_DSP111": 0, "F1_DSP112": 0},
        # {"F1_DSP111": 400, "F1_DSP112": 400},
        {"F1_DSP111": 500, "F1_DSP112": 500},
    ]

    # Configuration path
    cfg_path = pathlib.Path(__file__).absolute().parents[1] / "cfg_ncsu"

    # Iterate over the defined configurations
    for step in step_configs:
        for device, p in step.items():
            pq_map = {"P": p, "Q": get_q(p)}
            set_values(device, cfg_path, pq_map)
            # Pause for 1 second between DERs
            # time.sleep(0.5)
        # Pause for 1 second between each step
        # time.sleep(1)


if __name__ == "__main__":
    main()

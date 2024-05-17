import fabric2 as fab
import json
import math
import pathlib
import yaml

import api

read_params = ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]
write_params = ["CONTROL", "REAL_POWER", "REACTIVE_POWER"]


def main():
    COS_PHI = 0.95  # Power factor. Set in the coop design file

    P_map = {
        "F1_DSP111": 0,
        "F1_DSP112": 0,
        # "F3_DSP115": 0,
        # "F3_DSP116": 0,
        "GEN1-Banshee": 0,
        # "GEN2-Banshee": 0,
        # "GEN3-Banshee": 0,
    }

    PQ_map = {
        key: {"P": value, "Q": value * math.tan(math.acos(COS_PHI))}
        for key, value in P_map.items()
    }

    cfg_path = pathlib.Path(__file__).absolute().parents[1] / "cfg_ncsu"
    for key in PQ_map:
        path_to_file = cfg_path / f"{key}.yaml"
        assert path_to_file.is_file()
        with open(path_to_file, "r") as f:
            device_config = yaml.safe_load(f)

        protocol = device_config["Protocol"]
        ip = device_config["TCP"]["Address"]

        if protocol == "TCP":
            api.set_OP(key, PQ_map[key])
        elif protocol == "Serial":
            c = fab.Connection(ip)
            c.run("hostname")
            print(f"Send OP for {key} with {json.dumps(PQ_map[key])}")
            c.run(
                f"python3 ~/UC3_SET_OP_PNTS/scripts/api.py --der_name {key} --PQ_map '{json.dumps(PQ_map[key])}' --fun 'set'"
            )

            # api.set_OP(PQ_map)


if __name__ == "__main__":
    main()

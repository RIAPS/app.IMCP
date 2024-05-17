import fabric2 as fab
import pathlib
import yaml

import api


def main():

    DER_map = {
        "F1_DSP111",
        "F1_DSP112",
        "F3_DSP115",
        "F3_DSP116",
        "GEN1-Banshee",
        "GEN2-Banshee",
        "GEN3-Banshee",
    }

    cfg_path = pathlib.Path(__file__).absolute().parents[1] / "cfg_ncsu"
    for key in DER_map:
        path_to_file = cfg_path / f"{key}.yaml"
        assert path_to_file.is_file()
        with open(path_to_file, "r") as f:
            device_config = yaml.safe_load(f)

        protocol = device_config["Protocol"]
        ip = device_config["TCP"]["Address"]

        if protocol == "TCP":
            api.reset_OP(key)
        elif protocol == "Serial":
            c = fab.Connection(ip)
            c.run("hostname")
            print(f"Read Values for {key}")
            c.run(
                f"python3 ~/UC3_SET_OP_PNTS/scripts/api.py --der_name {key} --fun 'reset'"
            )


if __name__ == "__main__":
    main()

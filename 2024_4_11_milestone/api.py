import argparse
import json
import pathlib
import time
import yaml
from riaps.interfaces.modbus.ModbusInterface import ModbusInterface


# read_params = ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]
read_params = ["CONTROL", "P", "Q"]
PCC_read_params = [
    # "IS_GRID_CONNECTED_BIT",
    # "VA_RMS",
    # "FREQ",
    # "SYNCHK_FREQ_SLIP",
    # "SYNCHK_VOLT_DIFF",
    # "SYNCHK_ANG_DIFF",
    "P",
    "Q",
]

write_params = ["CONTROL", "REAL_POWER", "REACTIVE_POWER"]


def read_OP(key):
    cfg_path = pathlib.Path(__file__).absolute().parents[1] / "cfg_ncsu"

    path_to_file = cfg_path / f"{key}.yaml"
    assert path_to_file.is_file()

    mbi = ModbusInterface(path_to_file)

    with open(path_to_file, "r") as f:
        device_config = yaml.safe_load(f)

    if "PCC" in device_config["Name"]:
        params = PCC_read_params
    else:
        params = read_params

    print(f"Reading inital values from {key}")
    result = poll_modbus_parameters(mbi, params)

    # Check if the DER is started
    if result.get("CONTROL"):
        if result["CONTROL"]["values"][0] != 1:
            # Start the DER
            print(f"Setting {key} CONTROL to 1")
            results = mbi.write_modbus(parameter="CONTROL", values=[1])
            time.sleep(1)

            # Make sure the DER is started
            result = poll_modbus_parameters(mbi, read_params)
            assert (
                result["CONTROL"]["values"][0] == 1
            ), f"Control is {result['CONTROL']}"


def set_OP(key, PQ_map):
    cfg_path = pathlib.Path(__file__).absolute().parents[1] / "cfg_ncsu"

    path_to_file = cfg_path / f"{key}.yaml"
    assert path_to_file.is_file()

    mbi = ModbusInterface(path_to_file)

    print(f"Reading inital values from {key}")
    poll_modbus_parameters(mbi, read_params)

    # Set the DER
    print(f"Setting {key} to {PQ_map}")
    set_PQ(mbi, PQ_map["P"], PQ_map["Q"])
    time.sleep(1)

    # Check the new values
    poll_modbus_parameters(mbi, read_params)


def reset_OP(key):
    cfg_path = pathlib.Path(__file__).absolute().parents[1] / "cfg_ncsu"

    path_to_file = cfg_path / f"{key}.yaml"
    assert path_to_file.is_file()

    mbi = ModbusInterface(path_to_file)

    mbi.write_modbus(parameter="CONTROL", values=[0])
    # Check the new values
    poll_modbus_parameters(mbi, read_params)


def poll_modbus_parameters(modbus_interface, parameter_list):
    results = {}
    for parameter in parameter_list:
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert (
            modbus_result is not None
        ), f"Parameter {parameter} returned {modbus_result}"
        results[parameter] = modbus_result

    print(f"Polled {len(results)} parameters")
    for result in results:
        print(f'Param: {result}, Values:{results[result]["values"]}')
    return results


def set_PQ(mbi, op_P, op_Q):
    """
    Set the DER to the desired OP
    """
    results = mbi.write_modbus(parameter="REAL_POWER", values=[op_P])
    print(f"Real Power write outcome: {results}")
    results = mbi.write_modbus(parameter="REACTIVE_POWER", values=[op_Q])
    print(f"Reactive Power write outcome: {results}")


def set_from_output():

    my_map = {
        "BATTERY_7000_kWh": "F1_DSP111",
        "DG_3000_kW": "GEN1-Banshee",
    }

    with open("output.yaml", "r") as f:
        output = yaml.safe_load(f)

    design_id = 0
    design = output["designs"][design_id]["plant"]["design"]
    for bus in design:
        DERs_installed = design[bus]["DERs_installed"]
        if not DERs_installed:
            continue
        for der in DERs_installed:
            op_P, op_Q = DERs_installed[der]["OP"]
            model_name = DERs_installed[der]["MODEL_NAME"]

            if "DG" in model_name:
                # DGs are connected via TCP
                cfg_path = pathlib.Path(__file__).absolute().parents[2] / "cfg_ncsu"
            else:
                # Batteries are connected via serial
                cfg_path = pathlib.Path(__file__).absolute().parents[0] / "cfg_ncsu"

            path_to_file = cfg_path / f"{my_map[model_name]}.yaml"
            assert path_to_file.is_file()

            mbi = ModbusInterface(path_to_file)

            # Check initial values
            results = poll_modbus_parameters(
                modbus_interface=mbi, parameter_list=read_params
            )

            # Start the DER
            results = mbi.write_modbus(parameter="CONTROL", values=[1])
            print(f"Control write outcome: {results}")

            # See if the DER is started
            results = poll_modbus_parameters(
                modbus_interface=mbi, parameter_list=read_params
            )

            # Set the DER to the desired OP
            results = mbi.write_modbus(parameter="REAL_POWER", values=[op_P])
            print(f"Real Power write outcome: {results}")
            results = mbi.write_modbus(parameter="REACTIVE_POWER", values=[op_Q])
            print(f"Reactive Power write outcome: {results}")

            # Check the OP values
            results = poll_modbus_parameters(
                modbus_interface=mbi, parameter_list=read_params
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--der_name",
        type=str,
        required=True,
        help="Name of the DER to set OP for",
    )
    parser.add_argument(
        "--PQ_map",
        type=str,
        required=False,
        help="Dictionary of P and Q values to set for the DER",
    )
    parser.add_argument(
        "--fun",
        type=str,
        required=False,
        help="Function to call",
    )

    args = parser.parse_args()

    if args.fun == "read":
        read_OP(args.der_name)
    elif args.fun == "set":
        assert args.PQ_map is not None, "PQ_map is required"
        set_OP(args.der_name, json.loads(args.PQ_map))
    elif args.fun == "reset":
        reset_OP(args.der_name)

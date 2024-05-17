import modbus_tk
import pathlib
import pandas as pd
from functions.modbus import tcp as mb_tcp

from riaps.interfaces.modbus.config import load_config_paths
from riaps.interfaces.modbus.config import load_config_files


cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_typhoon"


def test_modbustk_execute():
    from modbus_tk import modbus_tcp
    import modbus_tk.defines as cst

    addr = "192.168.10.181"
    port = 502
    master = modbus_tcp.TcpMaster(addr, port)

    starting_address = 0
    length = 3
    data_fmt = ""

    result: tuple = master.execute(
        slave=1,
        function_code=cst.READ_HOLDING_REGISTERS,
        starting_address=starting_address,
        quantity_of_x=length,
        data_format=data_fmt,
    )

    print(f"result: {result}")

    result: tuple = master.execute(
        slave=1,
        function_code=cst.WRITE_MULTIPLE_REGISTERS,
        starting_address=2001,
        quantity_of_x=1,
        data_format="",
        output_value=[1],  # 0 means open 1 is closed
    )

    print(f"result: {result}")

    # result: tuple = master.execute(
    #     slave=1,
    #     function_code=cst.WRITE_MULTIPLE_REGISTERS,
    #     starting_address=2000,
    #     quantity_of_x=2,
    #     data_format=">I",
    #     output_value=[400],
    # )

    # print(f"result: {result}")


def test_modbus_interface():
    ders = ["F1_DSP111", "GEN1-Banshee"]
    der_parameters = [
        "FREQ",
        "VA_RMS",
        "P",
        "Q",
        "VREF",
        "WREF",
    ]
    relays = ["F1PCC"]
    relay_parameters = [
        "IS_GRID_CONNECTED_BIT",
        "VA_RMS",
        "FREQ",
        "SYNCHK_FREQ_SLIP",
        "SYNCHK_VOLT_DIFF",
        "SYNCHK_ANG_DIFF",
        "P",
        "Q",
    ]

    der_result, relay_result = mb_tcp(
        cfg_path,
        DERs=ders,
        DER_parameters=der_parameters,
        relays=relays,
        relay_parameters=relay_parameters,
    )

    print(f"ders: \n{pd.DataFrame.from_dict(der_result)}")
    print(f"relays: \n{pd.DataFrame.from_dict(relay_result)}")

    # Check that paths are configured correctly
    relay = "F1PCC"

    path_to_device_list = "./cfg_typhoon/RELAYF1.yaml"
    dl_pth = pathlib.Path(path_to_device_list).parents[0]

    device_config_paths, global_debug_mode = load_config_paths(path_to_device_list)
    dvc_path = pathlib.Path(device_config_paths[relay]).parents[0]

    assert (
        dl_pth.absolute() == dvc_path.absolute()
    ), f"path for {relay} is misconfigured"

    # User compare computed relay status against expectation
    controlled_relays = load_config_files(device_config_paths)

    relay_status_thresholds = controlled_relays[relay]["RELAY_STATUS_THRESHOLDS"]

    connected = (
        relay_result["F1PCC"]["IS_GRID_CONNECTED_BIT"]
        == relay_status_thresholds["GRID_CONNECTED"]
    )

    msg = "" if connected else "not"
    print(f"System believes grid is {msg}connected")

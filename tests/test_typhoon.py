import modbus_tk
import pathlib
import pandas as pd
from functions.modbus import tcp as mb_tcp

from riaps.interfaces.modbus.config import load_config_paths
from riaps.interfaces.modbus.config import load_config_files
import riaps.interfaces.modbus.ModbusInterface as ModbusInterface


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
        output_value=[0],  # 0 means open 1 is closed
    )

    print(f"result: {result}")


def test_run():
    pcc_mbi = ModbusInterface.ModbusInterface(f"{cfg_path}/F1PCC.yaml")
    b1_mbi = ModbusInterface.ModbusInterface(f"{cfg_path}/F1_DSP111.yaml")
    b2_mbi = ModbusInterface.ModbusInterface(f"{cfg_path}/F1_DSP112.yaml")
    dg_mbi = ModbusInterface.ModbusInterface(f"{cfg_path}/GEN1-Banshee.yaml")

    pcc_status = pcc_mbi.read_modbus("IS_GRID_CONNECTED_BIT")
    print(f"pcc_status: {pcc_status}")
    # Close PCC
    pcc_mbi.write_modbus("LOGIC", values=[1])
    # 1 is close, 3 is close and VF mode
    pcc_status = pcc_mbi.read_modbus("IS_GRID_CONNECTED_BIT")
    print(f"pcc_status: {pcc_status}")

    # ------ Energize DERs ----------------------------------
    input("Press enter to energize bess 1")
    b1_status = b1_mbi.read_modbus("CONTROL")
    print(f"b1_status: {b1_status}")
    b1_mbi.write_modbus("CONTROL", values=[1])
    b1_status = b1_mbi.read_modbus("CONTROL")
    print(f"b1_status: {b1_status}")

    input("Press enter to energize bess 2")
    b2_status = b2_mbi.read_modbus("CONTROL")
    print(f"b2_status: {b2_status}")
    b2_mbi.write_modbus("CONTROL", values=[1])
    b2_status = b2_mbi.read_modbus("CONTROL")
    print(f"b2_status: {b2_status}")

    # ------ Set values ----------------------------------
    input("Press enter to send PQ commands to bess 1")
    b1_P = b1_mbi.read_modbus("REAL_POWER")
    b1_Q = b1_mbi.read_modbus("REACTIVE_POWER")
    print(f"b1_P: {b1_P}")
    print(f"b1_Q: {b1_Q}")
    b1_mbi.write_modbus("REAL_POWER", values=[1000])
    b1_mbi.write_modbus("REACTIVE_POWER", values=[400])
    b1_P = b1_mbi.read_modbus("REAL_POWER")
    b1_Q = b1_mbi.read_modbus("REACTIVE_POWER")
    print(f"b1_P: {b1_P}")
    print(f"b1_Q: {b1_Q}")

    input("Press enter to send PQ commands to bess 2")
    b2_P = b2_mbi.read_modbus("REAL_POWER")
    b2_Q = b2_mbi.read_modbus("REACTIVE_POWER")
    print(f"b2_P: {b2_P}")
    print(f"b2_Q: {b2_Q}")
    b2_mbi.write_modbus("REAL_POWER", values=[1000])
    b2_mbi.write_modbus("REACTIVE_POWER", values=[400])
    b2_P = b2_mbi.read_modbus("REAL_POWER")
    b2_Q = b2_mbi.read_modbus("REACTIVE_POWER")
    print(f"b2_P: {b2_P}")
    print(f"b2_Q: {b2_Q}")

    # ------ DG ----------------------------------
    # input("Press enter to energize DG")
    # dg_status = dg_mbi.read_modbus("CONTROL")
    # print(f"b1_status: {dg_status}")
    # dg_mbi.write_modbus("CONTROL", values=[1])
    # dg_status = dg_mbi.read_modbus("CONTROL")
    # print(f"b1_status: {dg_status}")

    # input("Press enter to send PQ commands to DG")
    # dg_P = dg_mbi.read_modbus("REAL_POWER")
    # dg_Q = dg_mbi.read_modbus("REACTIVE_POWER")
    # print(f"b1_P: {dg_P}")
    # print(f"b1_Q: {dg_Q}")
    # dg_mbi.write_modbus("REAL_POWER", values=[1000])
    # dg_mbi.write_modbus("REACTIVE_POWER", values=[400])
    # dg_mbi.write_modbus("VOLTAGE", values=[1])
    # dg_mbi.write_modbus("FREQUENCY", values=[0.001])
    # dg_P = dg_mbi.read_modbus("REAL_POWER")
    # dg_Q = dg_mbi.read_modbus("REACTIVE_POWER")
    # print(f"b1_P: {dg_P}")
    # print(f"b1_Q: {dg_Q}")

    # CLEANUP
    input("Press Enter to set PQ to 0")
    b1_mbi.write_modbus("REAL_POWER", values=[0])
    b1_mbi.write_modbus("REACTIVE_POWER", values=[0])
    b2_mbi.write_modbus("REAL_POWER", values=[0])
    b2_mbi.write_modbus("REACTIVE_POWER", values=[0])
    dg_mbi.write_modbus("REAL_POWER", values=[0])
    dg_mbi.write_modbus("REACTIVE_POWER", values=[0])
    dg_mbi.write_modbus("VOLTAGE", values=[0])
    dg_mbi.write_modbus("FREQUENCY", values=[0])
    input("Press enter to shutdown DERs")
    b1_mbi.write_modbus("CONTROL", values=[0])
    b2_mbi.write_modbus("CONTROL", values=[0])
    dg_mbi.write_modbus("CONTROL", values=[0])
    input("Press enter to disconnect PCC")
    pcc_mbi.write_modbus("LOGIC", values=[0])


def test_modbus_interface():
    # ders = ["F1_DSP111", "F1_DSP112", "GEN1-Banshee"]
    ders = []
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

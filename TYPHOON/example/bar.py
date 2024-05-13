import pathlib
import riaps.interfaces.modbus.ModbusInterface as ModbusInterface


def poll_modbus_parameters(modbus_interface, parameter_list):
    results = {}
    for parameter in parameter_list:
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert (
            modbus_result is not None
        ), f"Parameter {parameter} returned {modbus_result}"
        results[parameter] = modbus_result
    return results


def modbustk_execute():
    from modbus_tk import modbus_tcp
    import modbus_tk.defines as cst

    print(f"run")
    addr = "192.168.10.230"
    port = 502
    master = modbus_tcp.TcpMaster(addr, port)

    starting_address = 0
    length = 26
    data_fmt = ""

    result: tuple = master.execute(
        slave=17,
        function_code=cst.READ_INPUT_REGISTERS,
        starting_address=starting_address,
        quantity_of_x=length,
        data_format=data_fmt,
    )

    print(f"result: {result}")


def test_modbus_tcp():
    cfg_path = f"{pathlib.Path(__file__).parents[0]}/cfg"
    der = "GEN1-Banshee"
    DER_params = [
        "IA_RMS",
        "IB_RMS",
        "IC_RMS",
        "VAB_RMS",
        "VBC_RMS",
        "VCA_RMS",
        "VA_RMS",
        "VB_RMS",
        "VC_RMS",
        "Pac",
        "FREQ",
        "Qac",
        "Pdc",
    ]

    path_to_file = f"{cfg_path}/{der}.yaml"
    mbi = ModbusInterface.ModbusInterface(path_to_file)
    print(f"\n {der}")
    result = poll_modbus_parameters(mbi, DER_params)
    for key in result:
        print(f"key: {key}, value: {result[key]['values']}")


if __name__ == "__main__":
    test_modbus_tcp()
    # modbustk_execute()

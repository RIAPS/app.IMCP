# cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"


import riaps.interfaces.modbus.ModbusInterface as ModbusInterface


def tcp(cfg_path, DERs=[], DER_parameters=[], relays=[], relay_parameters=[]):
    der_result = {}
    relay_result = {}

    for relay in relays:
        path_to_file = f"{cfg_path}/{relay}.yaml"
        mbi = ModbusInterface.ModbusInterface(path_to_file)
        print(f"\n {relay}")
        result = poll_modbus_parameters(
            modbus_interface=mbi, parameter_list=relay_parameters
        )
        relay_result[relay] = {}
        for key in result:
            relay_result[relay][key] = result[key]["values"][0]

    for der in DERs:
        path_to_file = f"{cfg_path}/{der}.yaml"
        mbi = ModbusInterface.ModbusInterface(path_to_file)
        print(f"\n {der}")
        result = poll_modbus_parameters(
            modbus_interface=mbi, parameter_list=DER_parameters
        )
        der_result[der] = {}
        for key in result:
            der_result[der][key] = result[key]["values"][0]

    return der_result, relay_result


def poll_modbus_parameters(modbus_interface, parameter_list):
    results = {}
    for parameter in parameter_list:
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert (
            modbus_result is not None
        ), f"Parameter {parameter} returned {modbus_result}"
        results[parameter] = modbus_result
    return results

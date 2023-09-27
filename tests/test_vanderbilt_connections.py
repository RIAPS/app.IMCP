import time

import riaps.interfaces.modbus.ModbusInterface as ModbusInterface
import riaps.interfaces.modbus.config as modbus_config
import logging
logging.basicConfig(format='%(asctime)s %(message)s')


def poll_modbus_parameters(modbus_interface, parameter_list):

    for parameter in parameter_list:
        print(f"poll parameter: {parameter}")
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert modbus_result is not None, f"Parameter {parameter} returned {modbus_result}"
        print(f"{parameter} output: {modbus_result['values']}")


def test_gen_on():
    path_to_configs = "/home/riaps/projects/RIAPS/app.MgManage_refactor/cfg_vanderbilt"
    path_to_file = f"{path_to_configs}/GEN1-Banshee.yaml"
    mb = ModbusInterface.ModbusInterface(path_to_file)

    parameters_to_poll = ["CONTROL", "P", "Q"]

    poll_modbus_parameters(mb,
                           parameter_list=parameters_to_poll)

    mb.write_modbus(parameter="CONTROL", values=[1])
    time.sleep(10)

    poll_modbus_parameters(mb,
                           parameter_list=parameters_to_poll)


def test_modbustk_execute():
    from modbus_tk import modbus_tcp
    import modbus_tk.defines as cst
    addr = "10.1.4.200"
    port = 502
    master = modbus_tcp.TcpMaster(addr, port)

    starting_address = 22
    length = 1
    data_fmt = ""

    result: tuple = master.execute(slave=1,
                                   function_code=cst.READ_INPUT_REGISTERS,
                                   starting_address=starting_address,
                                   quantity_of_x=length,
                                   data_format=data_fmt)

    print(f"result: {result}")


def test_gen_read():
    path_to_configs = "/home/riaps/projects/RIAPS/app.MgManage_refactor/cfg_vanderbilt"
    path_to_file = f"{path_to_configs}/GEN1-Banshee.yaml"

    mb = ModbusInterface.ModbusInterface(path_to_file)

    time.sleep(1)

    parameters_to_poll = ["FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]

    poll_modbus_parameters(mb,
                           parameter_list=parameters_to_poll)


def test_relay_read():
    path_to_configs = "/home/riaps/projects/RIAPS/app.MgManage_refactor/cfg_vanderbilt"
    path_to_file = f"{path_to_configs}/F1PCC.yaml"

    parameters_to_poll = ["IS_GRID_CONNECTED_BIT",
                          "VA_RMS",
                          "FREQ",
                          "SYNCHK_FREQ_SLIP",
                          "SYNCHK_VOLT_DIFF",
                          "SYNCHK_ANG_DIFF",
                          "P",
                          "Q"]

    poll_modbus_parameters(modbus_config_path=path_to_file,
                           parameter_list=parameters_to_poll)


def patched_load_config_files(device_config_paths):
    device_configs = {}
    print(f"device_name: {device_config_paths}")
    for device_name in device_config_paths:
        print(f"device_name: {device_name}")
    #     config_path = device_config_paths[device_name]
    #     return config_path
    #     device_configs[device_name] = modbus_config.load_config_file(config_path)
    # return device_configs


def test_foo_config():
    path_to_configs = "/home/riaps/projects/RIAPS/app.MgManage_refactor/cfg_vanderbilt"
    path_to_device_list = f"{path_to_configs}/RELAYF1.yaml"

    device_config_paths, global_debug_mode = modbus_config.load_config_paths(path_to_device_list)
    print(f"device_config_paths: {device_config_paths}")
    device_configs = modbus_config.load_config_files(device_config_paths)
    print(device_configs)

    # import sys
    # original_stdout = sys.stdout
    # sys.stdout = sys.__stdout__
    #
    # modbus_config.load_config_files = patched_load_config_files
    #
    # output = modbus_config.load_config_files(path_to_file)
    # print(f"output: {output}")
    #
    # sys.stdout = original_stdout

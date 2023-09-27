import json
import pathlib
import time
import riaps.interfaces.modbus.ModbusInterface as ModbusInterface


def test_opal():
    path_to_configs = f"{pathlib.Path(__file__).parents[1]}/cfg_vanderbilt"
    devices_to_monitor = {"F1PCC": ["IS_GRID_CONNECTED_BIT", "VA_RMS", "FREQ", "SYNCHK_FREQ_SLIP",
                                    "SYNCHK_VOLT_DIFF", "SYNCHK_ANG_DIFF", "P", "Q"],
                          "GEN1-Banshee": ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"],
                          "GEN2-Banshee": ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]}

    modbus_interfaces = {}
    for device in devices_to_monitor:
        path_to_file = f"{path_to_configs}/{device}.yaml"
        modbus_interfaces[device] = ModbusInterface.ModbusInterface(path_to_file)

    start_time = time.time()
    duration_seconds = 60 * 60 * 24
    end_time = start_time + duration_seconds

    file_name = f"{path_to_configs}/devices_to_monitor.csv"
    fh = open(file_name, "w")

    generators_running = False

    while end_time > time.time():
        for device in devices_to_monitor:
            for parameter in devices_to_monitor[device]:
                modbus_response = modbus_interfaces[device].read_modbus(parameter=parameter)
                # try to write modbus_response to csv file, if it fails close the file and stop the test
                try:
                    fh.write(f"{time.time()},{device},{parameter},{modbus_response['values'][0]}\n")
                except:
                    fh.close()
                    assert False, f"Failed to write to {file_name}"
        if not generators_running:
            modbus_interfaces["GEN1-Banshee"].write_modbus(parameter="CONTROL", values=[1])
            modbus_interfaces["GEN2-Banshee"].write_modbus(parameter="CONTROL", values=[1])
            generators_running = True
        fh.flush()
        time.sleep(10)

    fh.close()


def test_opal_2_json():
    path_to_configs = f"{pathlib.Path(__file__).parents[1]}/cfg_vanderbilt"
    devices_to_monitor = {"F1PCC": {"IS_GRID_CONNECTED_BIT": [], "VA_RMS": [], "FREQ": [], "SYNCHK_FREQ_SLIP": [],
                                    "SYNCHK_VOLT_DIFF": [], "SYNCHK_ANG_DIFF": [], "P": [], "Q": []},
                          "GEN1-Banshee": {"CONTROL": [], "FREQ": [], "VA_RMS": [],
                                           "P": [], "Q": [], "VREF": [], "WREF": []},
                          "GEN2-Banshee": {"CONTROL": [], "FREQ": [], "VA_RMS": [],
                                           "P": [], "Q": [], "VREF": [], "WREF": []}}

    devices_to_monitor = {"F1PCC": ["IS_GRID_CONNECTED_BIT", "VA_RMS", "FREQ", "SYNCHK_FREQ_SLIP",
                                    "SYNCHK_VOLT_DIFF", "SYNCHK_ANG_DIFF", "P", "Q"],
                          "GEN1-Banshee": ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"],
                          "GEN2-Banshee": ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]}


    modbus_interfaces = {}
    for device in devices_to_monitor:
        path_to_file = f"{path_to_configs}/{device}.yaml"
        modbus_interfaces[device] = ModbusInterface.ModbusInterface(path_to_file)

    modbus_interfaces["GEN1-Banshee"].write_modbus(parameter="CONTROL", values=[1])
    modbus_interfaces["GEN2-Banshee"].write_modbus(parameter="CONTROL", values=[1])

    start_time = time.time()
    duration_seconds = 60 * 60 * 24
    end_time = start_time + duration_seconds

    while end_time > time.time():
        for device in devices_to_monitor:
            for parameter in devices_to_monitor[device]:
                modbus_response = modbus_interfaces[device].read_modbus(parameter=parameter)
                devices_to_monitor[device][parameter].append(modbus_response["values"][0])
        time.sleep(10)

    # Write devices_to_monitor to json file
    json_file_name = f"{path_to_configs}/devices_to_monitor.json"
    with open(json_file_name, 'w') as outfile:
        json.dump(devices_to_monitor, outfile, indent=4)





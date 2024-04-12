
import os
import pathlib
import time
from riaps.interfaces.modbus.ModbusInterface import ModbusInterface


tcp_DERs = ["GEN1-Banshee"]
serial_DERs = ["F1_DSP111"]

read_params = ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]
write_params = ["CONTROL", "REAL_POWER", "REACTIVE_POWER"]

def poll_modbus_parameters(modbus_interface, parameter_list):
    results = {}
    for parameter in parameter_list:
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert (
            modbus_result is not None
        ), f"Parameter {parameter} returned {modbus_result}"
        results[parameter] = modbus_result
    return results

# Define a function to check if ttyS1 exists
def has_ttyS1_access():
    has_access = os.access("/dev/ttyS1", os.R_OK | os.W_OK)
    print(f"has_access: {has_access}")

    return has_access

if has_ttyS1_access():
    cfg_path = pathlib.Path(__file__).absolute().parents[0] / "cfg_ncsu"
    print(f"bbb cfg_path: {cfg_path}")
    DERs = serial_DERs
else:
    cfg_path = pathlib.Path(__file__).absolute().parents[2] / "cfg_ncsu"
    print(f"vm cfg_path: {cfg_path}")
    DERs = tcp_DERs

print(f"cfg_path: {cfg_path}")

for der in DERs:
    path_to_file = cfg_path / f"{der}.yaml"
    assert path_to_file.is_file()

    mbi = ModbusInterface(path_to_file)

    results = poll_modbus_parameters(
        modbus_interface=mbi, parameter_list=read_params
    )

    print(f"Polled {len(results)} parameters")
    for result in results:
        print(f'Param: {result}, Values:{results[result]["values"]}')

    
if True:
    
    for der in DERs:
        path_to_file = cfg_path / f"{der}.yaml"
        assert path_to_file.is_file()
        mbi = ModbusInterface(path_to_file)
        P = 600
        Q = 300
        results =  mbi.write_modbus(parameter="REAL_POWER", values=[P])
        print(f"Real Power write outcome: {results}")
        results =  mbi.write_modbus(parameter="REACTIVE_POWER", values=[Q]) 
        print(f"Reactive Power write outcome: {results}")


    # value = 0 # 0: stop 1: start
    # mbi.write_modbus(parameter="CONTROL", values=[value])
    for t in range(5):
        time.sleep(1)
        print(f"Slept for: {t}")

    for der in DERs:
        path_to_file = cfg_path / f"{der}.yaml"
        assert path_to_file.is_file()

        mbi = ModbusInterface(path_to_file)

        results = poll_modbus_parameters(
            modbus_interface=mbi, parameter_list=read_params
        )

        print(f"Polled {len(results)} parameters")
        for result in results:
            print(f'Param: {result}, Values:{results[result]["values"]}')

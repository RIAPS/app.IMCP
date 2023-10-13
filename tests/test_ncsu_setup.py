from modbus_tk import modbus_rtu
import os
import pathlib
import pytest
import time
import riaps.interfaces.modbus.ModbusInterface as ModbusInterface


def test_modbustk_execute():
    from modbus_tk import modbus_tcp
    import modbus_tk.defines as cst
    addr = "192.168.10.201"
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



def test_modbus_tcp():
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    DERs = ["GEN1-Banshee", "GEN2-Banshee", "GEN3-Banshee"]
    DER_parameters = ["FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]
    relays = ["F1PCC","F1108","F2PCC","F2217","F3PCC"]
    relay_parameters = ["IS_GRID_CONNECTED_BIT", "VA_RMS", "FREQ", "SYNCHK_FREQ_SLIP",
                        "SYNCHK_VOLT_DIFF", "SYNCHK_ANG_DIFF", "P", "Q"]

    for der in DERs:
        path_to_file = f"{cfg_path}/{der}.yaml"
        mbi =  ModbusInterface.ModbusInterface(path_to_file)
        print(f"\n {der}")
        poll_modbus_parameters(modbus_interface=mbi,
                               parameter_list=DER_parameters)
    for relay in relays:
        path_to_file = f"{cfg_path}/{relay}.yaml"
        mbi =  ModbusInterface.ModbusInterface(path_to_file)
        print(f"\n {relay}")
        poll_modbus_parameters(modbus_interface=mbi,
                               parameter_list=relay_parameters)



def poll_modbus_parameters(modbus_interface, parameter_list):
    results = {}
    for parameter in parameter_list:
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert modbus_result is not None, f"Parameter {parameter} returned {modbus_result}"
        results[parameter] = modbus_result
    return results


# Define a function to check if ttyS1 exists
def has_ttyS1_access():
    return os.access('/dev/ttyS1', os.R_OK | os.W_OK)

@pytest.fixture
@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def modbustk_serial():
    import serial
    import modbus_tk.modbus_rtu as modbus_rtu
    serial_connection = serial.Serial(port="/dev/ttyS1",
                                      baudrate=115200,
                                      bytesize=8,
                                      parity='N',
                                      stopbits=1,
                                      xonxoff=0)
    master = modbus_rtu.RtuMaster(serial_connection)
    master.set_timeout((1000 / 1000.0), use_sw_timeout=True)
    yield master
    master.close()

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_modbustk_serial_read(modbustk_serial):
    import modbus_tk.defines as cst

    starting_address = 2000  # CONTROL
    length = 1
    data_fmt = ""

    # starting_address = 22  # FREQ
    # length = 1
    # data_fmt = ""

    result: tuple = modbustk_serial.execute(slave=10,
                                            function_code=cst.READ_HOLDING_REGISTERS,
                                            starting_address=starting_address,
                                            quantity_of_x=length,
                                            data_format=data_fmt)
    
    print(f"Read control register result: {result}")


    print("Write control register")

    result=  modbustk_serial.execute(slave=10,
                                     function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                     starting_address=starting_address,
                                     quantity_of_x=length,
                                     data_format=data_fmt,
                                     output_value=[0],)
    
    print(f"Write control register result: {result}")
    

    result: tuple = modbustk_serial.execute(slave=10,
                                            function_code=cst.READ_HOLDING_REGISTERS,
                                            starting_address=starting_address,
                                            quantity_of_x=length,
                                            data_format=data_fmt)
    
    print(f"Read control register result: {result}")
    

# The DSP tests need to be run from the nodes connected via serial to the DSP.
def write_dsp(der, value):
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    path_to_file = f"{cfg_path}/{der}.yaml"
    mbi =  ModbusInterface.ModbusInterface(path_to_file)

    if value == "start":
        values = [1]
    elif value == "stop":
        values = [0]
    else:
        values = [value]
    mbi.write_modbus(parameter="CONTROL", values=values)

    
def read_dsp(der):
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    path_to_file = f"{cfg_path}/{der}.yaml"
    DER_parameters = ["CONTROL", "FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]
    
    mbi = ModbusInterface.ModbusInterface(path_to_file)

    results = poll_modbus_parameters(modbus_interface=mbi,
                                     parameter_list=DER_parameters)
    return results
    

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp():
    der = "F1_DSP111"
    results = read_dsp(der=der)
    started = results["CONTROL"]["values"][0] == 1
    print(f"CONTROL ON: {started}, P: {results['P']['values']}")

    write_dsp(der=der, value="stop" if started else "start")
    results = read_dsp(der=der)
    started = results["CONTROL"]["values"][0] == 1
    print(f"CONTROL ON: {started}, P: {results['P']['values']}")

    for i in range(6):
        time.sleep(10)
        results = read_dsp(der=der)
        started = results["CONTROL"]["values"][0] == 1
        print(f"CONTROL ON: {started}, P: {results['P']['values']}")

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_stop():
    der = "F1_DSP111"
    write_dsp(der=der, value="stop")


# Use the @pytest.mark.skipif decorator to skip the test if ttyS1 doesn't exist
@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_start_dsp_111():
    der = "F1_DSP111"
    write_dsp(der=der, value="start")

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_111():
    der = "F1_DSP111"
    results = read_dsp(der=der)
    print(results)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_112():
    der = "F1_DSP112"
    read_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_114():
    der = "F2_DSP114"
    read_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_115():
    der = "F3_DSP115"
    read_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_116():
    der = "F3_DSP116"
    read_dsp(der=der)


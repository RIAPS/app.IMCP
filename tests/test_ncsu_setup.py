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

def test_modbustk_serial():
    import serial
    import modbus_tk
    import modbus_tk.defines as cst
    import modbus_tk.modbus_rtu as modbus_rtu
    
    serial_connection = serial.Serial(port="/dev/ttyS1",
                                      baudrate=115200,
                                      bytesize=8,
                                      parity='N',
                                      stopbits=1,
                                      xonxoff=0)
    master = modbus_rtu.RtuMaster(serial_connection)
    master.set_timeout((1000 / 1000.0), use_sw_timeout=True)

    starting_address = 2000  # CONTROL
    length = 1
    data_fmt = ""

    print("Write control register")

    result=  master.execute(slave=10,
                                    function_code=cst.WRITE_MULTIPLE_REGISTERS,
                                    starting_address=starting_address,
                                    quantity_of_x=length,
                                    data_format=data_fmt,
                                    output_value=[1],)
    
    print(f"Write control register result: {result}")
    

    result: tuple = master.execute(slave=10,
                                    function_code=cst.READ_HOLDING_REGISTERS,
                                    starting_address=starting_address,
                                    quantity_of_x=length,
                                    data_format=data_fmt)
    
    print(f"Read control register result: {result}")
    

    starting_address = 22  # FREQ
    length = 1
    data_fmt = ""

    result: tuple = master.execute(slave=10,
                                    function_code=cst.READ_INPUT_REGISTERS,
                                    starting_address=starting_address,
                                    quantity_of_x=length,
                                    data_format=data_fmt)

    print(f"Read Freq result: {result}")

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
        
def test_modbus_serial():
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    DERs = ["F1_DSP111", "F1_DSP112", "F2_DSP114", "F3_DSP115", "F3_DSP116"]
    DER_parameters = ["FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]

    for der in DERs:
        path_to_file = f"{cfg_path}/{der}.yaml"
        mbi =  ModbusInterface.ModbusInterface(path_to_file)
        print(f"\n {der}")
        poll_modbus_parameters(modbus_interface=mbi,
                               parameter_list=DER_parameters)



def poll_modbus_parameters(modbus_interface, parameter_list):
    
    for parameter in parameter_list:
        print(f"poll parameter: {parameter}")
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert modbus_result is not None, f"Parameter {parameter} returned {modbus_result}"
        print(f"{parameter} output: {modbus_result['values']}")


# The DSP tests need to be run from the nodes connected via serial to the DSP.
def start_dsp(der):
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    path_to_file = f"{cfg_path}/{der}.yaml"
    mbi =  ModbusInterface.ModbusInterface(path_to_file)

    parameters_to_poll = ["CONTROL", "P", "Q"]

    # poll_modbus_parameters(modbus_interface=mbi, parameter_list=parameters_to_poll)

    mbi.write_modbus(parameter="CONTROL", values=[1])
    time.sleep(10)

    # poll_modbus_parameters(modbus_interface=mbi, parameter_list=parameters_to_poll)

    
def query_dsp(der):
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    path_to_file = f"{cfg_path}/{der}.yaml"
    DER_parameters = ["FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]
    
    mbi = ModbusInterface.ModbusInterface(path_to_file)

    poll_modbus_parameters(modbus_interface=mbi,
                           parameter_list=DER_parameters)
    

# Define a function to check if ttyS1 exists
def has_ttyS1_access():
    return os.access('/dev/ttyS1', os.R_OK | os.W_OK)

# Use the @pytest.mark.skipif decorator to skip the test if ttyS1 doesn't exist
@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_start_dsp_111():
    der = "F1_DSP111"
    start_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_111():
    der = "F1_DSP111"
    query_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_112():
    der = "F1_DSP112"
    query_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_114():
    der = "F2_DSP114"
    query_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_115():
    der = "F3_DSP115"
    query_dsp(der=der)

@pytest.mark.skipif(not has_ttyS1_access(), reason="No access to ttyS1")
def test_dsp_116():
    der = "F3_DSP116"
    query_dsp(der=der)


def test_gen_on():
    cfg_path = f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu"
    device = "GEN2-Banshee"
    path_to_file = f"{cfg_path}/{device}.yaml"
    mbi = ModbusInterface.ModbusInterface(path_to_file)

    parameters_to_poll = ["CONTROL", "P", "Q"]

    poll_modbus_parameters(modbus_interface=mbi, parameter_list=parameters_to_poll)

    mbi.write_modbus(parameter="CONTROL", values=[1])
    time.sleep(10)

    poll_modbus_parameters(modbus_interface=mbi, parameter_list=parameters_to_poll)

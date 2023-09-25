import json
import multiprocessing
import pathlib
import os
import pytest
import queue
import time

from riaps.ctrl.ctrl import Controller
from riaps.utils.config import Config

import riaps.interfaces.modbus.ModbusInterface as ModbusInterface

def poll_modbus_parameters(modbus_config_path, parameter_list):
    
    modbus_interface =  ModbusInterface.ModbusInterface(modbus_config_path)

    for parameter in parameter_list:
        print(f"poll parameter: {parameter}")
        modbus_result = modbus_interface.read_modbus(parameter=parameter)
        assert modbus_result is not None, f"Parameter {parameter} returned {modbus_result}"
        print(f"{parameter} output: {modbus_result['values']}")


# @pytest.mark.skip
def test_sanity():
    assert True


def test_mqtt(test_logger):
    import riaps.interfaces.mqtt.MQTT as MQTT
    import yaml

    cfg_path = "/home/riaps/my_riaps_apps/app.MgManage_refactor/cfg_ncsu/mqtt.yaml"
    cfg = MQTT.load_mqtt_config(path_to_config=cfg_path)

    thread = MQTT.MQThread(test_logger, cfg)
    assert thread.topics
    thread.mqtt_client()
    thread.mqtt_connect()

    topic = "riaps/ctrl"
    connected = False
    fill = "red" if connected else "green"
    for relay_uid in cfg["riaps_to_mqtt_mapping"]:
        diagram_id = cfg["riaps_to_mqtt_mapping"][relay_uid]
   
        payload = [
            {
                "command": "update_style",
                "selector": f"#{diagram_id}",
                "style": {"fill": fill}
            },
            {
                "command": "update_text",
                "selector": f"#{diagram_id}_text",
                "text": f"P: {round(1234.56789, 4)}"
            }
        ]
        data = json.dumps(payload)
        time.sleep(0.1)
        thread.send(topic, data, qos=0)

    test_logger.warning(thread.broker)
    assert thread.broker


def test_opal_read_relay():

    path_to_file = "/home/riaps/my_riaps_apps/app.MgManage_refactor/cfg_ncsu/F1PCC.yaml"
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

def test_opal_read_DER():
    path_to_configs = "/home/riaps/my_riaps_apps/app.MgManage_refactor/cfg_ncsu"
    path_to_file = f"{path_to_configs}/GEN1-Banshee.yaml"

    parameters_to_poll = ["FREQ", "VA_RMS", "P", "Q", "VREF", "WREF"]

    poll_modbus_parameters(modbus_config_path=path_to_file,
                           parameter_list=parameters_to_poll)


@pytest.fixture
def required_clients():
    operators = ['192.168.10.122']
    relays = ['192.168.10.119', '192.168.10.120', '192.168.10.121']
    dsps = ['192.168.10.111', '192.168.10.112', '192.168.10.114', '192.168.10.115', '192.168.10.116']
    gens = ['192.168.10.113', '192.168.10.117', '192.168.10.118']
    required_clients = operators + relays + dsps + gens
    yield required_clients


def test_clients(required_clients):
    c = Controller(port=8888, script="-")
    c.startDht()
    c.startService()

    # wait 10 seconds for clients to be discovered
    known_clients = []
    timeout = time.time() + 10
    while not set(required_clients).issubset(set(known_clients)):
        
        if time.time() >= timeout:
            assert False, "Timeout while waiting for nodes to be discovered"
        
        known_clients = c.getClients()
        print(f"known clients: {known_clients}")
        time.sleep(1)

    # Stop controller
    print("Stop controller")
    c.stop()
    print("controller stopped")


def test_app(log_server, required_clients):

    the_config = Config()
    c = Controller(port=8888, script="-")

    if True:
        
        app_folder = pathlib.Path(__file__).parents[1]
        c.setAppFolder(app_folder)
        app_name = c.compileApplication("appMgManage_banshee.riaps", app_folder)
        depl_file = "appMgManage_banshee_ncsu.depl"
        also_app_name = c.compileDeployment(depl_file)

        # start
        # c.startRedis()
        c.startDht()
        c.startService()

        # wait for clients to be discovered
        known_clients = []
        while not set(required_clients).issubset(set(known_clients)):
            known_clients = c.getClients()
            print(f"known clients: {known_clients}")
            time.sleep(1)

        # load application
        app_loaded = c.loadByName(app_name)
        print(f"app loaded? {app_loaded}")
        # launch application
        print("launch app")
        app_launched = c.launchByName(app_name)
        print(f"app launched? {app_launched}")
        # downloadApp (line 512). Does the 'I' mean 'installed'?
        # launchByName (line 746)

        print(f"All nodes have all subscriptions active")

        done = input("Provide input when ready to stop")

        # Halt application
        print("Halt app")
        is_app_halted = c.haltByName(app_name)
        # haltByName (line 799).
        print(f"app halted? {is_app_halted}")

        # Remove application
        print("remove app")
        c.removeAppByName(app_name)  # has no return value.
        # removeAppByName (line 914).
        print("app removed")

        # Stop controller
        print("Stop controller")
        c.stop()
        print("controller stopped")

        assert True

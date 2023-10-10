import datetime
import functools
import inspect
import json
import pathlib
import psutil
import pytest
import queue
import re
import time
import threading

import riaps_fixtures_library.utils as utils
import riaps.test_suite.test_api as test_api
from event_thread_handlers.single_feeder_24 import watch24 as single_24
from event_thread_handlers.full_24 import watch24 as full_24

# --------------- #
# -- Config -- #
# --------------- #
single = functools.partial(single_24, nodes_to_watch=["20_", "36_"], operator_node_id="172.21.20.20")
vanderbilt_config = {"VM_IP": "172.21.20.70",
                     "mqtt_config": f"{pathlib.Path(__file__).parents[1]}/cfg_vanderbilt/mqtt.yaml",
                     "app_folder_path": pathlib.Path(__file__).parents[1],
                     "app_file_name": "IMCP_SingleFeeder_VU.riaps",
                     "depl_file_name": "IMCP_SingleFeeder_VU.depl",
                     "event_thread_handler": single}


full = functools.partial(full_24, nodes_to_watch=["122_", "113_"], operator_node_id="192.168.10.122")
ncsu_config = {"VM_IP": "192.168.10.106",
               "mqtt_config": f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu/mqtt.yaml",
               "app_folder_path": pathlib.Path(__file__).parents[1],
               "app_file_name": "IMCP_Banshee_NCSU.riaps",
               "depl_file_name": "IMCP_Banshee_NCSU.depl",
               "test_mqtt_depl_file_name": "IMCP_Banshee_NCSU_test.depl",
               "event_thread_handler": full}

configs = {"vu": vanderbilt_config,
           "ncsu": ncsu_config}

test_cfg = configs["ncsu"]

mqtt_config = {
    "broker_ip": test_cfg["VM_IP"],
    "broker_port": 1883,
    "broker_keepalive": 60
}


# --------------- #
# -- LOG TESTS -- #
# --------------- #

def test_testslogger(testslogger):
    testslogger.info(f"Test started at {time.time()}")
    for handler in testslogger.handlers:
        print(f"flushing handler: {handler}")
        handler.flush()
        
    for ix in range(10):
        testslogger.info(f"Test {ix}")
        time.sleep(1)
    testslogger.info(f"Test stopped at {time.time()}")
    log_file_path = f"{pathlib.Path(__file__).parents[1]}/tests/test_logs"

    assert pathlib.Path(f"{log_file_path}/debug.log").exists(), "Expected file does not exist"

def test_testslogger_thread(testslogger):
    def threaded_logger_function(logger):
        logger.info(f"Threaded logger started at {time.time()}")
        for ix in range(10):
            logger.info(f"Threaded logger {ix}")
            time.sleep(1)
        logger.info(f"Threaded logger stopped at {time.time()}")

    testslogger.info(f"Test started at {time.time()}")
    for handler in testslogger.handlers:
        print(f"handler: {handler}")

    threaded_logger = threading.Thread(target=threaded_logger_function, args=(testslogger,))
    threaded_logger.start()
        
    for ix in range(10):
        testslogger.info(f"Test {ix}")
        time.sleep(1)
    testslogger.info(f"Test stopped at {time.time()}")
    log_file_path = f"{pathlib.Path(__file__).parents[1]}/tests/test_logs"

    assert pathlib.Path(f"{log_file_path}/debug.log").exists(), "Expected file does not exist"


@pytest.mark.parametrize('log_server', [{'server_ip': test_cfg["VM_IP"],
                                         'log_config_path': f"{test_cfg['app_folder_path']}/riaps-log.conf"}],
                         indirect=True)
def test_log_server(log_server):
    print(f"test_log_server: {log_server}")


# ---------------- #
# -- TODO TESTS -- #
# ---------------- #
# Write a test that checks the ip in the depl file for the permitted traffic 
#  host all{
#         network 192.168.10.106;
#     }


def test_mqtt_config():
    from riaps.interfaces.mqtt import MQTT
    riaps_mqtt_config_file = test_cfg["mqtt_config"]
    riaps_mqtt_config = MQTT.load_mqtt_config(riaps_mqtt_config_file)
    riaps_mqtt_ip = riaps_mqtt_config["broker_connect_config"]["host"]
    test_mqtt_ip = mqtt_config["broker_ip"]

    error_msg = (f"The IP address in the riaps mqtt_config file {riaps_mqtt_ip}"
                 f" does not match the ip specified in the test {test_mqtt_ip}")

    assert riaps_mqtt_ip == test_mqtt_ip, error_msg


# ------------------------- #
# -- RESOURCE MONITORING -- #
# ------------------------- #

def save_to_csv(data, filename):
    # Get the current timestamp
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Append the timestamp to the data
    data_with_timestamp = f"{timestamp}\n{data}"

    #TODO: Create file if it doesn't exist
    # Write the data to the CSV file
    with open(filename, 'a', newline='') as csv_file:
        csv_file.write(data_with_timestamp)


def test_monitoring(fabric_group):
    test_data = str(pathlib.Path(__file__).parents[0]) + "/test_data"

    samples_collected = 0

    process_to_monitor = 2031
    assert psutil.pid_exists(process_to_monitor), f"Process {process_to_monitor} does not exist"

    while True:
        if not psutil.pid_exists(process_to_monitor):
            print(f"Process {process_to_monitor} no longer exists")
            break

        results = fabric_group.run('free -m', hide=True)
        for conn in results:
            memory_utilization = results[conn].stdout
            save_to_csv(memory_utilization, f'{test_data}/memory_utilization_{conn.host}.csv')

        results = fabric_group.run('ps aux --sort=-%mem | head -11', hide=True)
        for conn in results:
            top_memory_processes = results[conn].stdout
            save_to_csv(top_memory_processes, f'{test_data}/top_memory_processes_{conn.host}.csv')
        samples_collected += 1
        print(f"Collected {samples_collected} samples")
        time.sleep(60)


# ---------------- #
# -- MQTT TESTS -- #
# ---------------- #
@pytest.mark.parametrize('log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
@pytest.mark.parametrize('mqtt_client', [mqtt_config], indirect=True)
def test_mqtt_2_riaps_communication(log_server, mqtt_client):
    # assert that test_cfg["test_mqtt_depl_file_name"] exists
    assert pathlib.Path(
        f"{test_cfg['app_folder_path']}/{test_cfg['test_mqtt_depl_file_name']}").exists(), \
        "Expected file does not exist"

    app_folder_path = test_cfg["app_folder_path"]
    app_file_name = test_cfg["app_file_name"]
    depl_file_name = test_cfg["test_mqtt_depl_file_name"]

    # gets expected clients from the depl file.
    client_list = utils.get_client_list(file_path=f"{app_folder_path}/{depl_file_name}")
    print(f"client list: {client_list}")

    controller, app_name = test_api.launch_riaps_app(app_folder_path=app_folder_path,
                                                     app_file_name=app_file_name,
                                                     depl_file_name=depl_file_name,
                                                     database_type="dht",
                                                     required_clients=client_list)

    key = input(
        "Wait until app starts then press a key to start the DERs or q to quit.\n"
        "(check server_logs/<ip of system operator target>_app.log for this message: 'MQThread no new message')")
    if key == "q":
        test_api.terminate_riaps_app(controller, app_name)
        print(f"Test complete at {time.time()}")
        return

    task = {"StartStop": 1}
    mqtt_client.publish(topic="mg/event",
                        payload=json.dumps(task),
                        qos=0)

    time.sleep(1)
    test_api.terminate_riaps_app(controller, app_name)
    print(f"Test complete at {time.time()}")


# -------------------------- #
# -- GUI DRIVEN APP TESTS -- #
# -------------------------- #
@pytest.mark.parametrize('platform_log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
@pytest.mark.parametrize('log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
@pytest.mark.parametrize('mqtt_client', [mqtt_config], indirect=True)
def test_app_with_gui(platform_log_server, log_server, mqtt_client):
    # TODO: Check that depl file `host all` has the correct ip address

    app_folder_path = test_cfg["app_folder_path"]
    app_file_name = test_cfg["app_file_name"]
    depl_file_name = test_cfg["depl_file_name"]

    client_list = utils.get_client_list(file_path=f"{app_folder_path}/{depl_file_name}")
    print(f"client list: {client_list}")

    controller, app_name = test_api.launch_riaps_app(
        app_folder_path=app_folder_path,
        app_file_name=app_file_name,
        depl_file_name=depl_file_name,
        database_type="dht",
        required_clients=client_list
    )

    input("Press a key to terminate the app\n")
    test_api.terminate_riaps_app(controller, app_name)
    print(f"Test complete at {time.time()}")


# --------------------------- #
# -- TEST DRIVEN APP TESTS -- #
# --------------------------- #

def next_command(logger, mqtt_client, data):
    logger.info(f"Wait for 60 seconds before executing command {data}")
    for ix in range(6):
        logger.info(f"Waited for {ix * 10} seconds")
        time.sleep(10)
    logger.info(f"Execute command: {data}")
    mqtt_client.publish(topic="mg/event",
                        payload=json.dumps(data),
                        qos=0)


class EventQMonitorThread(threading.Thread):
    def __init__(self, handler, logger=None):
        super().__init__()
        self.is_running = False
        self.stop_event = threading.Event()
        self.event_q_handler = threading.Thread(target=handler, kwargs={"stop_event": self.stop_event})
        self.event_q_handler.daemon = True
        self.logger = logger

    def run(self):
        try:
            self.is_running = True
            self.event_q_handler.start()
            while self.is_running:
                self.logger.debug(f"EventQMonitorThread is alive: {self.event_q_handler.is_alive()}") if self.logger is not None else None
                time.sleep(1)
        except Exception as e:
            print(f"Exception in EventQThread: {e}")
        finally:
            self.logger.info(f"EventQMonitorThread is stopping") if self.logger is not None else None
            self.logger.info(f"event_q alive?: {self.event_q_handler.is_alive()}") if self.logger is not None else None

    def stop(self):
        self.stop_event.set()
        self.event_q_handler.join()
        self.is_running = False
        
        

def partial_with_missing_args(func, *args, **kwargs):
    partial_func = functools.partial(func, *args, **kwargs)
    
    def missing_args(*args, **kwargs):
        signature = inspect.signature(func)
        bound_args = signature.bind_partial(*args, **kwargs)
        
        missing_params = [param for param, value in bound_args.arguments.items() if value is param.default]
        
        return partial_func, missing_params
    
    return missing_args


@pytest.mark.parametrize('platform_log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
@pytest.mark.parametrize('log_server', indirect=True,
                         argvalues=[{'server_ip': test_cfg["VM_IP"],
                                     'log_config_path': f"{test_cfg['app_folder_path']}/riaps-log.conf"}])
@pytest.mark.parametrize('mqtt_client', [mqtt_config], indirect=True)
def test_app(testslogger, platform_log_server, log_server, mqtt_client):
    # TODO: Add something to quit the test if opal is not running.
    app_folder_path = test_cfg["app_folder_path"]
    app_file_name = test_cfg["app_file_name"]
    depl_file_name = test_cfg["depl_file_name"]
    partial_event_thread_handler = test_cfg["event_thread_handler"]

    event_q = queue.Queue()
    task_q = queue.Queue()
    end_time = time.time() + 24 * 60 * 60

    # logger, event_q, task_q, end_time, stop_event

    event_thread_handler = functools.partial(partial_event_thread_handler, 
                                             logger=testslogger, 
                                             event_q=event_q, 
                                             task_q=task_q,
                                             end_time=end_time)
    
    # partial_event_thread_handler_signature = inspect.signature(partial_event_thread_handler)
    # event_thread_handler_signature = inspect.signature(event_thread_handler)
    # partial_event_thread_handler_parameters = partial_event_thread_handler_signature.parameters
    # event_thread_handler_parameters = event_thread_handler_signature.parameters

    # for param_name, param_info in partial_event_thread_handler_parameters.items():
    #     print(f"partial Parameter: {param_name}")
    #     print(f"partial Default Value: {param_info.default}")

    # for param_name, param_info in event_thread_handler_parameters.items():
    #     print(f"Parameter: {param_name}")
    #     print(f"Default Value: {param_info.default}")
    
  
    try: 
        log_file_path = str(pathlib.Path(__file__).parents[1]) + "/server_logs"
        log_file_observer_thread = test_api.FileObserverThread(event_q, folder_to_monitor=log_file_path, logger=None)
        log_file_observer_thread.start()

        
        event_q_monitor_thread = EventQMonitorThread(handler=event_thread_handler, logger=None)
        event_q_monitor_thread.start()

        

        client_list = utils.get_client_list(file_path=f"{app_folder_path}/{depl_file_name}")
        testslogger.info(f"client list: {client_list}")

        controller = None
        app_name = None
        controller, app_name = test_api.launch_riaps_app(
            app_folder_path=app_folder_path,
            app_file_name=app_file_name,
            depl_file_name=depl_file_name,
            database_type="dht",
            required_clients=client_list,
            logger=testslogger
        )

        finished = False
        time_of_last_task = 0
        max_seconds_between_tasks = 600
        first_task_start_timer = time.time()
        max_seconds_until_first_task = 600
    
        while not finished:
            now = time.time()
            if int(now) % 10 == 0:
                if not log_file_observer_thread.is_alive():
                    testslogger.info(f"Log file observer is not alive. Restarting.")
                    log_file_observer_thread.stop()
                    log_file_observer_thread = test_api.FileObserverThread(event_q, folder_to_monitor=log_file_path)
                    log_file_observer_thread.start()

                if not event_q_monitor_thread.is_alive():
                    testslogger.info(f"event_q_monitor_thread is not alive. Restarting.")
                    event_q_monitor_thread.stop()
                    event_q_monitor_thread = EventQMonitorThread(None, event_q, task_q, end_time=end_time, handler=event_thread_handler)
                    event_q_monitor_thread.start()

            try:
                task = task_q.get(timeout=1)
            except queue.Empty:
                if int(now) % 10 == 0:
                    testslogger.info(f"No tasks received in the last 10 seconds")
                if time_of_last_task == 0:
                    seconds_waiting_for_first_task = now - first_task_start_timer
                    if seconds_waiting_for_first_task > max_seconds_until_first_task:
                        testslogger.info(f"Test timed out after {seconds_waiting_for_first_task} seconds")
                        finished = True
                else:
                    seconds_since_last_task = now - time_of_last_task
                    if seconds_since_last_task > max_seconds_between_tasks:
                        testslogger.info(f"Time between tasks is too long: {seconds_since_last_task}")
                        finished = True
                continue

            if time_of_last_task == 0:
                time_of_last_task = time.time()
            time_since_last_task = time.time() - time_of_last_task
            time_of_last_task = time.time()
            if time_since_last_task > max_seconds_between_tasks:
                testslogger.info(f"Time between tasks is too long: {time_since_last_task}")
                finished = True
                continue

            if task == "terminate":
                finished = True
            else:
                next_command(testslogger, mqtt_client, task)
    except KeyboardInterrupt:
        testslogger.info(f"KeyboardInterrupt")

    if controller is not None and app_name is not None:
        test_api.terminate_riaps_app(controller, app_name)
    
    event_q_monitor_thread.stop()
    log_file_observer_thread.stop()
    testslogger.info(f"Test complete at {time.time()}")
    

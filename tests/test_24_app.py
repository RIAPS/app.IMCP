import csv
import datetime
import json
import pathlib
import psutil
import pytest
import queue
import re
import netifaces
import time
import threading

import riaps_fixtures_library.utils as utils
import riaps.test_suite.test_api as test_api


# --------------- #
# -- Config -- #
# --------------- #
vanderbilt_config = {"VM_IP": "172.21.20.70",
                     "mqtt_config": f"{pathlib.Path(__file__).parents[1]}/cfg_vanderbilt/mqtt.yaml",
                     "node_ids": ["20_", "36_"],
                     "SystemOperator": "172.21.20.20",
                     "app_folder_path": pathlib.Path(__file__).parents[1],
                     "app_file_name": "IMCP_SingleFeeder_VU.riaps",
                     "depl_file_name": "IMCP_SingleFeeder_VU.depl"}

ncsu_config = {"VM_IP": "192.168.10.106",
               "mqtt_config": f"{pathlib.Path(__file__).parents[1]}/cfg_ncsu/mqtt.yaml",
               "node_ids": ["122_", "113_"],
               "SystemOperator": "192.168.10.122",
               "app_folder_path": pathlib.Path(__file__).parents[1],
               "app_file_name": "IMCP_Banshee_NCSU.riaps",
               "depl_file_name": "IMCP_Banshee_NCSU.depl",
               "test_mqtt_depl_file_name": "IMCP_Banshee_NCSU_test.depl"}

configs =  {"vandy": vanderbilt_config,
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
def write_test_log(msg):
    log_dir_path = pathlib.Path(__file__).parents[1] / 'tests' / 'test_logs'
    log_dir_path.mkdir(parents=True, exist_ok=True)
    with open(f"{log_dir_path}/test_24_app_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.utcnow()} | {msg}\n")


def write_test_error_log(msg):
    log_file_path = f"{pathlib.Path(__file__).parents[1]}/presentation/data"
    with open(f"{log_file_path}/test_24_app_error_log.txt", "a") as log_file:
        log_file.write(f"{datetime.datetime.utcnow()} | {msg}\n")

def test_write_test_log():
    write_test_log(f"Test started at {time.time()}")
    time.sleep(1)
    write_test_log(f"Test stopped at {time.time()}")
    log_file_path = f"{pathlib.Path(__file__).parents[1]}/tests/test_logs"

    assert pathlib.Path(f"{log_file_path}/test_24_app_log.txt").exists(), "Expected file does not exist"


@pytest.mark.parametrize('log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
def test_log_server(log_server):
    print(f"test_log_server: {log_server}")
    file_path = test_cfg["app_folder_path"] / "riaps-log.conf"

    pattern = r'server_host = "(\d+\.\d+\.\d+\.\d+)"'
    # Open the app riaps-log.conf file to check that ips match
    with file_path.open("r") as file:
        file_content = file.read()
        match = re.search(pattern, file_content)

        if match:
            ip_address = match.group(1)

    error_msg = (f"The IP address in the riaps-log.conf file {ip_address}"
                 f" does not match the VM's IP address {test_cfg['VM_IP']}")
    assert ip_address == test_cfg["VM_IP"], error_msg

# ---------------- #
# -- TODO TESTS -- #
# ---------------- #
# Write a test that checks the ip in the depl file for the permitted traffic 
#  host all{
#         network 192.168.10.139;
#     }

def test_mqtt_config():
    from riaps.interfaces.mqtt import MQTT
    riaps_mqtt_config_file = test_cfg["mqtt_config"]
    riaps_mqtt_config = MQTT.load_mqtt_config(riaps_mqtt_config_file)
    riaps_mqtt_ip = riaps_mqtt_config["broker_connect_config"]["host"]
    test_mqtt_ip = mqtt_config["broker_ip"]

    error_msg = (f"The IP address in the riaps mqtt_config file {riaps_mqtt_ip}"
                 f" does not match the ip specfied in the test {test_mqtt_ip}")
    
    assert riaps_mqtt_ip == test_mqtt_ip, error_msg



# ------------------------- #
# -- RESOURCE MONITORING -- #
# ------------------------- #

def save_to_csv(data, filename):
    # Get the current timestamp
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Append the timestamp to the data
    data_with_timestamp = f"{timestamp}\n{data}"

    # Write the data to the CSV file
    with open(filename, 'a', newline='') as csv_file:
        csv_file.write(data_with_timestamp)

    # Split the output into lines and save it to a CSV file
    # # lines = data.strip().split('\n')
    # with open(filename, 'w', newline='') as csv_file:
    #     csv_writer = csv.writer(csv_file)
    #     for line in lines:
    #         csv_writer.writerow(line.split())


def test_monitoring(fabric_group):
    test_data = str(pathlib.Path(__file__).parents[0]) + "/test_data"

    # samples_required = 2
    samples_collected = 0
    # while samples_collected < samples_required:

    process_to_monitor = 117965

    while True:
        if not psutil.pid_exists(process_to_monitor):
            print(f"Process {process_to_monitor} does not exist")
            break

        # if samples_collected == 2:
        #     print(f"Collected {samples_collected} samples")
        #     break

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
    assert pathlib.Path(f"{test_cfg['app_folder_path']}/{test_cfg['test_mqtt_depl_file_name']}").exists(), "Expected file does not exist"

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

    key = input("Wait until app starts (check server_logs/<ip of system operator target>_app.log for this message: MQThread no new message) then press a key to start the DERs or q to quit.\n")
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

def next_command(mqtt_client, data):
    write_test_log(f"Wait for 60 seconds before executing command {data}")
    for ix in range(6):
        write_test_log(f"Waited for {ix*10} seconds")
        time.sleep(10)
    write_test_log(f"Execute command: {data}")
    mqtt_client.publish(topic="mg/event",
                        payload=json.dumps(data),
                        qos=0)


class EventQMonitorThread(threading.Thread):
    def __init__(self, event_q, task_q, end_time):
        super().__init__()
        self.is_running = False
        self.event_q_handler = threading.Thread(target=watch24, args=(event_q, task_q, end_time))
        self.event_q_handler.daemon = True

    def run(self):
        try:
            self.is_running = True
            self.event_q_handler.start()
            while self.is_running:
                time.sleep(1)
        except Exception as e:
            print(f"Exception in EventQThread: {e}")
        finally:
            self.event_q_handler.join()

    def stop(self):
        self.is_running = False


@pytest.mark.parametrize('platform_log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
@pytest.mark.parametrize('log_server', [{'server_ip': test_cfg["VM_IP"]}], indirect=True)
@pytest.mark.parametrize('mqtt_client', [mqtt_config], indirect=True)
def test_app(platform_log_server, log_server, mqtt_client):
    # TODO: Add something to quit the test if opal is not running.
    event_q = queue.Queue()
    task_q = queue.Queue()
    log_file_path = str(pathlib.Path(__file__).parents[1]) + "/server_logs"
    log_file_observer_thread = test_api.FileObserverThread(event_q, folder_to_monitor=log_file_path)
    log_file_observer_thread.start()

    end_time = time.time() + 24 * 60 * 60
    event_q_monitor_thread = EventQMonitorThread(event_q, task_q, end_time=end_time)
    event_q_monitor_thread.start()

    app_folder_path = test_cfg["app_folder_path"]
    app_file_name = test_cfg["app_file_name"]
    depl_file_name = test_cfg["depl_file_name"]

    client_list = utils.get_client_list(file_path=f"{app_folder_path}/{depl_file_name}")
    write_test_log(f"client list: {client_list}")

    controller, app_name = test_api.launch_riaps_app(
        app_folder_path=app_folder_path,
        app_file_name=app_file_name,
        depl_file_name=depl_file_name,
        database_type="dht",
        required_clients=client_list
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
                write_test_log(f"Log file observer is not alive. Restarting.")
                log_file_observer_thread.stop()
                log_file_observer_thread = test_api.FileObserverThread(event_q, folder_to_monitor=log_file_path)
                log_file_observer_thread.start()

            if not event_q_monitor_thread.is_alive():
                write_test_log(f"event_q_montior_thread is not alive. Restarting.")
                event_q_monitor_thread.stop()
                event_q_monitor_thread = EventQMonitorThread(event_q, task_q, end_time=end_time)
                event_q_monitor_thread.start()

        try:
            task = task_q.get(timeout=1)
        except queue.Empty:
            if time_of_last_task == 0:
                seconds_waiting_for_first_task = now - first_task_start_timer
                if seconds_waiting_for_first_task > max_seconds_until_first_task:
                    write_test_log(f"Test timed out after {seconds_waiting_for_first_task} seconds")
                    finished = True
            else:
                seconds_since_last_task = now - time_of_last_task
                if seconds_since_last_task > max_seconds_between_tasks:
                    write_test_log(f"Time between tasks is too long: {seconds_since_last_task}")
                    finished = True
            continue

        if time_of_last_task == 0:
            time_of_last_task = time.time()
        time_since_last_task = time.time() - time_of_last_task
        time_of_last_task = time.time()
        if time_since_last_task > max_seconds_between_tasks:
            write_test_log(f"Time between tasks is too long: {time_since_last_task}")
            finished = True
            continue

        if task == "terminate":
            finished = True
        else:
            next_command(mqtt_client, task)

    test_api.terminate_riaps_app(controller, app_name)
    write_test_log(f"Test complete at {time.time()}")


def watch24(event_q, task_q, end_time):
    files = {}
    start_time = time.time()
    datetime_start = datetime.datetime.fromtimestamp(start_time)
    datetime_end = datetime.datetime.fromtimestamp(end_time)
    duration_seconds = end_time - start_time

    task_count = 0
    last_active_state = None
    current_target_state = "GRID-TIED"
    no_errors = True

    write_test_log(f"Watchdog started at {datetime_start}, "
                   f"will run for {duration_seconds} seconds until {datetime_end}")
    while end_time > time.time() and no_errors:
        try:
            event_source = event_q.get(10)  #
        except queue.Empty:
            write_test_log(f"File event queue is empty")
            continue

        if ".log" not in event_source:  # required to filter out the directory events
            continue

        file_name = pathlib.Path(event_source).name
        file_data = files.get(file_name, None)
        if file_data is None:
            file_handle = open(event_source, "r")
            files[file_name] = {"fh": file_handle, "offset": 0}
        else:
            file_handle = file_data["fh"]

        if not any(node_id in file_name for node_id in test_cfg["node_ids"]):
            continue  # Not interested in this file

        for line in file_handle:
            files[file_name]["offset"] += len(line)
            if "ERROR" in line:
                no_errors = False
                write_test_log(f"Encountered an ERROR in {file_name} at {time.time()}: {line}")
                break
            elif "exception" in line:
                no_errors = False
                write_test_log(f"Encountered an exception in {file_name} at {time.time()}: {line}")
                break
            if "app_event" not in line:
                continue

            try:
                ignore1, level, timestamp, pid, json_msg, ignore2 = line.split("::")
            except ValueError:
                no_errors = False
                write_test_log(f"Encountered a malformed line in {file_name} at {time.time()}: {line}")
                break

            msg = json.loads(json_msg)

            if test_cfg["SystemOperator"] in file_name and "COMPONENT_INITIALIZED" in msg["app_event"]:
                task = {"StartStop": 1}
                task_q.put(task)
                task = {"active": 400, "reactive": 300}
                task_q.put(task)
                write_test_log(f"System operator is initialized, start the generators")
            elif "FAIL" in msg["app_event"]:
                action = msg["app_event"]["FAIL"]
                if action == "ISLAND":
                    write_test_log(f"Failed to open PCC relay. Retry task {task_count}| {line}")
                    task_count -= 1
                    current_target_state = "GRID-TIED"
                elif action == "RESYNC":
                    write_test_log(f"Failed to close PCC relay. Retry task {task_count}| {line}")
                    task_count -= 1
                    current_target_state = "ISLANDED"
                elif action == "DISCONNECT":
                    write_test_log(f"Failed to disconnect relay | {line}")
                    current_target_state = "ISLANDED"
                    # TODO: I know these last two are clearly not correct.
                    #  I need to figure out how to get the correct state.
                elif action == "CONNECT":
                    write_test_log(f"Failed to connect relay. Retry task {task_count}| {line}")
                    task_count -= 1
                    current_target_state = "ISLANDED"

            elif "ENTER_STATE" in msg["app_event"]:

                write_test_log(f"ENTERED STATE: {msg['app_event']['ENTER_STATE']} at {timestamp} "
                               f"caused by {msg['app_event']['trigger']}. "
                               f"Current task: {task_count} "
                               f"Current target state: {current_target_state}")
                task = None
                if "LOCAL-CONTROL" in msg["app_event"].get("ENTER_STATE"):
                    write_test_log(f"Generator is in local control, enable secondary control")
                    task_q.put({"SecCtrlEnable": 1})
                elif "GRID-TIED" in msg["app_event"].get("ENTER_STATE"):
                    write_test_log(f"Grid is tied, open the PCC relay")
                    last_active_state = "GRID-TIED"
                    if current_target_state == "GRID-TIED":
                        task = {"event": "relay_click", "requestedRelay": "F1PCC", "requestedAction": "OPEN"}
                        task_count += 1
                        current_target_state = "ISLANDED"

                elif "ISLANDED" in msg["app_event"].get("ENTER_STATE"):
                    write_test_log(f"Grid is islanded, close the PCC relay")
                    last_active_state = "ISLANDED"
                    if current_target_state == "ISLANDED":
                        task = {"event": "relay_click", "requestedRelay": "F1PCC", "requestedAction": "CLOSE"}
                        task_count += 1
                        current_target_state = "GRID-TIED"

                if task is not None:

                    if task_count in [2, 3]:
                        # This will disable secondary control, causing the generator to go back to local control
                        # where secondary control will be re-enabled.j
                        write_test_log(f"Task {task_count}. Queue task: {task}")
                        task_q.put({"SecCtrlEnable": 0})
                        task_q.put(task)
                    elif task_count == 5:
                        task_count = 0
                        current_target_state = last_active_state  # I probably don't need this as well as the task count reset when a task fails.
                        # This is necessary because I want to make sure that the generator is back in "GRID-TIED" before I disable the control and when it comes back online it will be in "GRID-TIED" and correctly set the current_target_state to ISLANDED as well as add the OPEN relay command to the queue. In other words, we're going back to the beginning of the loop and need to set the values back to their initial state.
                        write_test_log(f"Task {task_count}. Skip task: {task}")
                        task_q.put({"SecCtrlEnable": 0})
                    else:
                        write_test_log(f"Task {task_count}. Queue task: {task}")
                        task_q.put(task)

                write_test_log(f"task_q: {list(task_q.queue)}")

    task_q.put("terminate")


import datetime
import time
import pytest
import re
import paho.mqtt.client as paho_mqtt_client
import riaps.interfaces.mqtt.MQTT as MQTT


@pytest.fixture
def test_logger():
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    return logger


@pytest.fixture
def mqtt_client(test_logger, request):
    params = request.param
    broker_ip = params["broker_ip"]
    port = params["broker_port"]
    keepalive = params["broker_keepalive"]

    def on_connect(client, userdata, flags, rc):
        error_string = paho_mqtt_client.error_string(rc)
        print(f"on_connect at {time.time()} error string: {error_string}")
        client.subscribe("test/mqtt")
        client.subscribe("mg/event")

    def on_disconnect(client, userdata, rc):
        error_string = paho_mqtt_client.error_string(rc)
        print(f"on_disconnect at {time.time()} error string: {error_string}")
        # client.reconnect()

    def on_publish(client, userdata, mid):

        print(f"{datetime.datetime.utcnow()} test's on_publish: {mid}")

    def on_message(client, userdata, msg):
        print(f"{datetime.datetime.utcnow()} test's on_message: {msg.topic} {str(msg.payload)})")

    test_client = paho_mqtt_client.Client()
    test_client.on_connect = on_connect
    test_client.on_disconnect = on_disconnect
    test_client.on_publish = on_publish
    test_client.on_message = on_message
    test_client.connect(broker_ip, port, keepalive)

    test_client.loop_start()

    yield test_client

    test_client.loop_stop()



@pytest.fixture
def riaps_mqtt_client(test_logger, request):
    params = request.param
    path_to_config = params["path_to_config"]
    cfg = MQTT.load_mqtt_config(path_to_config=path_to_config)

    thread = MQTT.MQThread(test_logger, cfg)
    thread.mqtt_client()
    thread.mqtt_connect()
    thread.start()
    thread.activate()
    yield thread, cfg
    thread.deactivate()
    thread.terminate()
    thread.join()


import re
import socket


def get_ip_address(hostname):
    try:
        interface = "eth0"
        # Use socket to resolve the IP address
        ip_address = socket.gethostbyname_ex(hostname)
        print(ip_address)
        for ip in ip_address[2]:
            return ip
    except socket.gaierror:
        return None


def get_client_list(file_path):
    client_names = []
    ip_addresses = []

    # Regular expression pattern to match lines with desired information
    pattern = r'on\s*\((.*?)\)\s*(\w+)_ACTOR'

    with open(file_path, 'r') as file:
        for line in file:
            # Remove leading and trailing whitespaces
            line = line.strip()
            # Skip lines that start with '//'
            if line.startswith('//'):
                continue
            # Search for matches in the line using the pattern
            matches = re.findall(pattern, line)
            for match in matches:
                # Split the matched portion to extract client names and IP addresses
                parts = match[0].split(',')
                for part in parts:
                    part = part.strip()
                    if part:
                        # Check if it's a valid IP address
                        try:
                            socket.inet_aton(part)
                            ip_addresses.append(part)
                        except socket.error:
                            client_names.append(part)

    # Resolve IP addresses for client names
    resolved_ip_addresses = {}
    for client_name in client_names:
        ip_address = get_ip_address(client_name)
        if ip_address:
            resolved_ip_addresses[client_name] = ip_address

    print("Client Names:", client_names)
    print("Resolved IP Addresses:", resolved_ip_addresses)
    ip_addresses.extend(resolved_ip_addresses.values())
    print("IP Addresses:", ip_addresses)
    return ip_addresses


if __name__ == '__main__':
    import pathlib
    # use pathlib to get to the grandparent folder
    app_folder_path = pathlib.Path(__file__).parent.parent.parent.absolute()
    print(app_folder_path)
    depl_file_name = "IMCP_Banshee_NCSU.depl"
    file_path = f"{app_folder_path}/{depl_file_name}"
    get_client_list(file_path=file_path)



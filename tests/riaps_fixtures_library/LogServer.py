import multiprocessing
import netifaces
import pytest
import queue
import re
from riaps.logger.server import AppLogServer
from riaps.logger.server import PlatformLogServer
import riaps.logger.drivers.factory as driver_factory


@pytest.fixture(scope='module')
def log_server(request):
    params = request.param
    ip = params["server_ip"]
    log_config_path = params["log_config_path"]

    # Check if ip configured in test is valid
    host_ips = []
    for interface in netifaces.interfaces():
        for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
            host_ips.append(link['addr'])
    print(host_ips)

    assert ip in host_ips, "Configured ip does not exist on host."

    # Check that the ip in the riaps-log.conf file matches the ip of the VM
    pattern = r'server_host = "(\d+\.\d+\.\d+\.\d+)"'
    with open(log_config_path, "r") as file:
        file_content = file.read()
        match = re.search(pattern, file_content)
        if match:
            ip_address = match.group(1)

    error_msg = (f"The IP address in the riaps-log.conf file {ip_address}"
                 f" does not match the VM's IP address {ip}")
    assert ip_address == ip, error_msg

    # Start the log server
    driver_type = "file"
    aserver = (ip, 9021)
    q = queue.Queue()
    driver = driver_factory.get_driver(driver_type=driver_type, session_name="app")
    app_log_server = AppLogServer(server_address=aserver,
                                  driver=driver,
                                  q=q)

    p = multiprocessing.Process(target=app_log_server.serve_until_stopped,
                                name="riaps.logger.app",
                                daemon=False)

    p.start()

    yield p

    p.terminate()
    p.join()


@pytest.fixture(scope='module')
def platform_log_server(request):
    params = request.param
    ip = params["server_ip"]

    driver_type = "file"
    pserver = (ip, 9020)
    q = queue.Queue()
    driver = driver_factory.get_driver(driver_type=driver_type, session_name="platform")
    log_server = PlatformLogServer(server_address=pserver,
                                   driver=driver,
                                   q=q)

    p = multiprocessing.Process(target=log_server.serve_until_stopped,
                                name="riaps.logger.platform",
                                daemon=False)

    p.start()

    yield p

    p.terminate()
    p.join()

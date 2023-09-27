import multiprocessing
import netifaces
import pytest
import queue
from riaps.logger.server import AppLogServer
from riaps.logger.server import PlatformLogServer
import riaps.logger.drivers.factory as driver_factory


@pytest.fixture(scope='module')
def log_server(request):
    params = request.param
    ip = params["server_ip"]

    host_ips = []
    for interface in netifaces.interfaces():
        for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
            host_ips.append(link['addr'])
    print(host_ips)

    assert ip in host_ips, "Configured ip does not exist on host."

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

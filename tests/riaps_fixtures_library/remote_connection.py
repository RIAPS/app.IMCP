import pytest
import fabric2 as fabric
from time import sleep


def rsync_put(c, local_path, remote_host, remote_path):
    c.local(f"rsync -avz {local_path} {remote_host}:{remote_path}")


def run_command_with_retry(fabric_group, command, retries=3, retry_interval=10):
    for attempt in range(retries + 1):
        try:
            result = fabric_group.run(command)
            return result
            # break  # The command executed successfully, exit the loop
        except Exception as e:
            print(f"Exception occurred during the test: {e}")
            print("Attempting to reestablish connections mid-test...")
            fabric_group.reconnect(1)  # Start with the first attempt
            # Retry the failed command after a successful reconnection
            print(f"Retrying command: {command}")
            sleep(retry_interval)
            continue


class CustomThreadingGroup(fabric.ThreadingGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_hosts = [args[0]]
        self._original_config = kwargs.get('config')

    def reconnect(self, retries=5, interval=10):
        for attempt in range(retries + 1):
            try:
                self.close()
                print(f"close successful.")
                group = CustomThreadingGroup(*self._original_hosts, config=self._original_config)
                print("Reconnection successful.")
                return group
            except Exception as e:
                if attempt < retries:
                    print(f"Reconnection failed: {e}")
                    print(f"Retrying in {interval} seconds...")
                    sleep(interval)
                else:
                    raise Exception("Maximum retries reached. Failed to reconnect.")


@pytest.fixture(scope='module')
def setup_remote_tmux(fabric_group):
    # The local path to the Python script containing the function
    local_script_path = "/home/riaps/projects/RIAPS/app.MgManage_refactor/tests/fmlib"

    # The remote path where the script will be copied to
    remote_script_path = "/home/riaps/tmp_remote_pytest"

    # Transfer the local script to the remote server
    for connection in fabric_group:
        print(f'connection: {connection}, host: {connection.host}')
        rsync_put(connection, local_script_path, connection.host, remote_script_path)
        print(f'connection: {connection}')

    # The name of the tmux session to create
    session_name = "my_session"
    window_name = "main"

    # Command to create a new tmux session
    command = f"tmux new-session -d -s {session_name} -n {window_name}"
    fabric_group.run(command, hide=True)

    yield fabric_group, remote_script_path, session_name, window_name

    # Close the tmux session after the tests
    try:
        tmux_command = f"tmux kill-session -t {session_name}"
        results = fabric_group.run(tmux_command, hide=True)

        for connection, result in results.items():
            print(f'connection: {connection}, command: {tmux_command}, result: {result}')
    except Exception as e:
        print(f"Encountered exception while closing tmux session: {e}")


@pytest.fixture(scope="module")
def fabric_group(request):
    def create_group():
        config = fabric.Config(
            overrides={'connect_kwargs': {'key_filename': '/home/riaps/.ssh/id_rsa'}})
        hosts = ['riaps@172.21.20.20', 'riaps@172.21.20.37', 'riaps@172.21.20.36', 'riaps@172.21.20.38']
        return CustomThreadingGroup(*hosts, config=config)

    group = create_group()

    def fin():
        group.close()

    request.addfinalizer(fin)

    try:
        yield group
    except Exception as e:
        print(f"NetworkError occurred: {e}")
        print("Attempting to reestablish connections...")
        group.reconnect(1)  # Start with the first attempt

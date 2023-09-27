import pytest
import time
from riaps_fixtures_library.remote_connection import run_command_with_retry


# # Test using the remote_group fixture with different remote_hosts
# @pytest.mark.parametrize("remote_group", [["riaps@172.21.20.40"]], indirect=True)
def test_fabric_operations(fabric_group):
    # Your test code using the `fabric_group` fixture
    result = fabric_group.run("ls -l")
    i = input("Enter to continue")
    result = fabric_group.run("ls -l")


def test_ip_link_down(setup_remote_tmux):

    remote_group, remote_script_path, session_name, window_name = setup_remote_tmux

    # The name of the Python function to be called
    function_name = "network_interface_down"

    # Command to run the Python script from within the tmux session
    python_command = f'python3 {remote_script_path}/fmlib/faults.py -f {function_name}'
    tmux_command = f"tmux send-keys -t {session_name} '{python_command}' Enter"
    results = remote_group.run(tmux_command, hide=True)

    for connection, result in results.items():
        print(f'connection: {connection}, command: {function_name}, result: {result}')

    # Test termination conditions
    notable_events = ["calling function"]
    termination_events = ["network interface up"]
    finished = False

    # Command to capture the output of the tmux session
    tmux_command = f"tmux capture-pane -p -t '{window_name}.0' -S -"
    # Wait for the termination event to occur
    while not finished:
        print(f"tmux_command: {tmux_command}")
        results = remote_group.run(tmux_command, hide=True)

        for connection, result in results.items():
            print(f'connection: {connection}')
            for line in result.stdout.splitlines():
                if any(event in line for event in termination_events):
                    print(f'line: {line}')
                    finished = True
                if any(event in line for event in notable_events):
                    print(f'line: {line}')
        if not finished:
            print(f"sleeping for 5 seconds")
            time.sleep(5)


def test_power_failure(setup_remote_tmux):
    remote_group, remote_script_path, session_name, window_name = setup_remote_tmux
    # The name of the Python function to be called
    function_name = "simulate_power_failure"

    python_command = f'sudo python3 {remote_script_path}/fmlib/faults.py -f {function_name}'
    tmux_command = f"tmux send-keys -t {session_name} '{python_command}' Enter"
    results = remote_group.run(tmux_command, hide=True)

    for connection, result in results.items():
        print(f'connection: {connection}, command: {tmux_command}, result: {result}')

    # Test termination conditions

    finished = False
    command = "uptime"
    while not finished:
        print(f"command: {command}")
        results = remote_group.run(command)
        print(f"results: {results}")

        i = input("Enter to continue")

        results = run_command_with_retry(remote_group, command, 5, 5)
        print(f"results: {results}")

        finished = True

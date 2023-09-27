# Project Title

A clear and concise title that describes your project.

## Table of Contents

- [Project Description](#project-description)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Examples](#examples)
- [Contributing](#contributing)
  - [Bug Reports](#bug-reports)
  - [Feature Requests](#feature-requests)
  - [Pull Requests](#pull-requests)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Project Description

Provide a comprehensive overview of your project. Explain its purpose, why it exists, and any relevant context. You can also include a brief list of key features.

## Getting Started

Explain how to get your project up and running. Include details about prerequisites and installation instructions.

### Prerequisites

Before you begin, ensure you have met the following requirements:

- [**RIAPS Development Host**](https://github.com/RIAPS/riaps-integration/blob/master/riaps-x86runtime/README.md)
- [**RIAPS Target Node**](https://github.com/RIAPS/riaps-integration/blob/master/riaps-node-runtime/README.md)
- Ensure that the mqtt broker is running:
    ```bash
    $ sudo systemctl status flashmq.service
    flashmq.service - FlashMQ MQTT server
     Loaded: loaded (/lib/systemd/system/flashmq.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2023-09-21 10:11:45 CDT; 4h 21min ago
    ```
- Ensure that the mqtt broker allows anonymous connections:
    - add `allow_anonymous true` to the file `/etc/flashmq/flashmq.conf` 
    - if it is not there, after adding it, run `sudo systemctl restart flashmq.service`
- Add node-red flow to create dashboard.
    1. Start node red with `node-red` in the terminal
    1. Open two browser tabs to:
        - `http://127.0.0.1:1880/`
        - `http://127.0.0.1:1880/ui/`
    1. Copy the contents of `GUI/flow5.json`
    1. In the `http://127.0.0.1:1880/` tab click the three horizontal bars in the top right corner and select `Import` or press `ctrl-i`
    ![install_mqtt](README_images/node-red-3bars.PNG) 
    1. Paste the contents `GUI/flow5.json` into the text field and click `Import`
    ![install_mqtt](README_images/node-red-import.PNG)
    1. Click the red `Deploy` button
    1. Switch to the `http://127.0.0.1:1880/ui/` tab where you should see the dashboard.
    ![install_mqtt](README_images/node-red-dashboard.PNG)
    
 

### Installation

With RIAPS properly installed and configured the other dependencies can be satisfied on all target nodes simultaneously using the `riaps_fab` command.
Tmux is used to improve robustness of the install commands, in case the Development Host loses connection with the target node before the installation is complete. The status of the install on a given node can be monitored by accessing a target node via ssh and running `tmux attach -t installdep`; this will attach to the tmux session. To detach from the tmux session use the key sequence `CTRL-b,d` (press ctrl and b, release and press d).
- **Host only Dependencies**:
  * fabric and fabric2
  ```bash
  sudo python3 -m pip install 'fabric<2.0' fabric2
  ```
  * [RIAPS test suite](https://github.com/RIAPS/test-suite)
  ```bash
  sudo python3 -m pip install git+https://github.com/RIAPS/test-suite.git
  ```
  * [Watchdog](https://github.com/gorakhargosh/watchdog)
  ```bash
  sudo python3 -m pip install watchdog
  ```

- **Host and Target Dependencies**:
  * Numpy: 
  ```bash 
  riaps_fab sys.run:'"tmux new-session -d -s install_numpy sudo\ python3\ -m\ pip\ install\ numpy\ "' 
  ```
  * [RIAPS modbus interface](https://github.com/RIAPS/interface.modbus.libs):
  ```bash
  riaps_fab sys.run:'"tmux new-session -d -s installdep sudo\ python3\ -m\ pip\ install\ git+https://github.com/RIAPS/interface.modbus.libs.git\ "'
  ```

  * [RIAPS mqtt interface](https://github.com/RIAPS/interface.mqtt):
  ```bash
  riaps_fab sys.run:'"tmux new-session -d -s installdep sudo\ python3\ -m\ pip\ install\ git+https://github.com/RIAPS/interface.mqtt.git"'
  ```
  ![install_mqtt](README_images/install_mqtt.PNG) 
  * [modbus-tk](https://github.com/ljean/modbus-tk)
  ```bash
  riaps_fab sys.run:'"tmux new-session -d -s installdep sudo\ python3\ -m\ pip\ install\ modbus-tk"'
  ```
  * [pytest](https://docs.pytest.org/en/7.1.x/getting-started.html)
  ```bash
  riaps_fab sys.run:'"tmux new-session -d -s installdep sudo\ python3\ -m\ pip\ install\ pytest"'
  ```

These can be installed on all target nodes simultaneously using the `riaps_fab` command. For example to install `numpy` from the command line on the Development Host you would run:
```bash
riaps_fab sys.run:'"tmux new-session -d -s install_numpy sudo\ python3\ -m\ pip\ install\ numpy\ "'
```
(Note: Installing numpy on a BBB will take several hours.)


### Verify Installation and configuration

1. **Start Opal**
  `Load` and `Execute` the OPAL-RT microgrid model. 
  ![start opal](README_images/rtlab_interface.PNG) 
1. **Test modbus connection**
    Run test and check that it passed and output a result (e.g., `result: (6024,)`).
    ```bash
    pytest -vs tests/test_ncsu_setup.py::test_modbustk_execute
    ```
    ![test modbustk](README_images/test_modbus-tk.PNG) 
1. **Test modbus tcp configurations**
    This ensures that all the parameters we care about for the application can be read from the simulation.
    ```bash
    pytest -vs tests/test_ncsu_setup.py::test_modbus_tcp
    ```
    ![example modbustcp resonse](README_images/test_opal_modbustcp_response.PNG) 
1. **Test modbus serial configuration**
    This test must be run from a target node that has a serial connection.
    The NCSU testbed has BeagleBone Black target nodes connected to DSP boards.
    1. First run the `sync_to_nodes.sh` to transfer the test script and config files to the target nodes to test. 
    1. SSH into the target node.
    1. Run the test:
    ```bash
    TODO
    ```
1. **Test that the test logger works**
    ```bash
    pytest -vs tests/test_24_app.py::test_write_test_log
    ```
1. **Test the log server**
    This test helps make sure that the test configuration is valid for the Development host and is consistent with the configuration in `riaps-log.conf`.
    ```bash
    pytest -vs tests/test_24_app.py::test_log_server
    ```
1. **Test the mqtt configuration**
    ```bash
    pytest -vs tests/test_24_app.py::test_mqtt_config
    ```

1. **Test that the mqtt communications are working between the test and app**
    This is an interactive test that starts the System Operator which listens for mqtt messages.
    There are 5 phases, 1) app startup, 2) Send `mg/event b'{"StartStop": 1}'` 3) Send `mg/event b'{"active": 400, "reactive": 300}'` 4) send `mg/event b'{"SecCtrlEnable": 1}'` 5) app teardown. 
    Between each phase the app waits for user input. This app makes use of the `log_server` so the output of the System Operator can be found in `server_logs/<ip_of_target_node>_app.log`. 
    If the app is running properly the content of the log file should include things like `Message from broker` e.g.,:
    ```bash
    ::[info]::[20:23:38,877]::[5703]::Message from broker: mg/event b'{"StartStop": 1}'::
    ::[info]::[20:23:38,879]::[5703]::on_trigger():{'StartStop': 1}::
    ::[info]::[20:23:38,881]::[5703]::{"timestamp": 1695327818.8807783, "level": "info", "module": "MQTT", "function": "on_trigger", "line": 29, "message": "on_trigger()", "app_event": "RECEIVED MESSAGE FROM MQTT BROKER"}::
    ::[info]::[20:23:38,884]::[5677]::
    System Operator.py - on_gui_sub
    msg {'StartStop': 1}::
    ::[info]::[20:23:38,885]::[5677]::
    System Operator.py - on_gui_sub
    self.control_values {'StartStop': 1, 'GridTiedOp': 0, 'SecCtrlEnable': 0, 'SecCtrlAngleEnable': 0, 'RegulationSignal': 0, 'RegulationSignal2': 0}::
    ::[info]::[20:23:38,886]::[5677]::
    OPAL_CTRL_MANAGER.py send_operator_msg
    msg: ( sender = "OPAL",
    type = "regD",
    msgcounter = 1,
    opalParams = ["StartStop", "GridTiedOp", "SecCtrlEnable", "SecCtrlAngleEnable", "RegulationSignal", "RegulationSignal2"],
    opalValues = [1, 0, 0, 0, 0, 0],
    requestedRelay = "NONE",
    requestedAction = "NONE",
    timestamp = 1695327818.8863797 )::
    ```


    A successful run from the pytest terminal looks like this:
    ```bash
    $ pytest -vs tests/test_24_app.py::test_mqtt_2_riaps_communication
    =========== test session starts =============
    platform linux -- Python 3.8.10, pytest-7.4.2, pluggy-1.3.0 -- /usr/bin/python3
    cachedir: .pytest_cache
    rootdir: /home/riaps/projects/RIAPS/app.MgManage_refactor/tests
    configfile: pytest.ini
    plugins: libtmux-0.15.7
    collected 1 item                                                                                                                                                                                                                                  

    tests/test_24_app.py::test_mqtt_2_riaps_communication[mqtt_client0-log_server0] ['127.0.0.1', '192.168.10.106', '10.0.2.15']
    on_connect at 1695327714.7804117 error string: No error.
    Client Names: []
    Resolved IP Addresses: {}
    IP Addresses: ['192.168.10.122']
    client list: ['192.168.10.122']
    Compiling app: appMgManage_banshee.riaps
    Compiling deployment: test.depl
    known_clients: []
    known_clients: []
    known_clients: []
    known_clients: []
    known_clients: ['192.168.10.122', '192.168.10.112', '192.168.10.120', '192.168.10.114', '192.168.10.113', '192.168.10.121', '192.168.10.119', '192.168.10.116', '192.168.10.111', '192.168.10.115', '192.168.10.118', '192.168.10.117']
    loading application: appMgManage
    Error: git tag failed
    I 192.168.10.122 appMgManage
    is_app_loaded: True
    launching application: appMgManage
    L 192.168.10.122 appMgManage SYSTEM_OPERATOR_ACTOR ['--config', './cfg_ncsu/OPAL-Device.yaml', '--mqtt_config', './cfg_ncsu/mqtt.yaml', '--mqtt_subsample_rate', '5']
    is_app_launched: True
    Wait until app starts then press a key to start the DERs or q to quit.

    Once the DERs start, press a key to set the power regulation or q to quit.
    2023-09-21 20:23:38.877847 test's on_publish: 3
    2023-09-21 20:23:38.878045 test's on_message: mg/event b'{"StartStop": 1}')

    Press a key to enable secondary control or q to quit.
    2023-09-21 20:23:43.065367 test's on_publish: 4
    2023-09-21 20:23:43.065711 test's on_message: mg/event b'{"active": 400, "reactive": 300}')

    Press a key to terminate the app
    2023-09-21 20:23:46.177066 test's on_publish: 5
    2023-09-21 20:23:46.177280 test's on_message: mg/event b'{"SecCtrlEnable": 1}')

    Halt app
    H 192.168.10.122 appMgManage SYSTEM_OPERATOR_ACTOR
    app halted? True
    remove app
    Error: git tag failed
    R appMgManage 
    app removed
    Stop controller
    controller stopped
    Test complete at 1695327833.3781416
    PASSED
    ```

If that all works, congratulations! The app will probably run. 


## Usage

### Start the application

1. Start node-red
1. Open two browser tabs to:
    1. `http://127.0.0.1:1880/`
    1. `http://127.0.0.1:1880/ui/`
1. `Load` and `Execute` the microgrid from RT-Lab. Make sure that in the `ModbusComs` subsystem the two `ModbusOrSimulated` (one at the top and the other at the bottom) toggles are set to 1, otherwise the control sent from the app is not received by the model. 
![node-red-running](README_images/banshee-matlab.PNG) 
![node-red-running](README_images/modbusOrSimulatedHighlights.PNG) 

1. Start the application
    ```bash
    pytest -vs tests/test_24_app.py::test_app_with_gui
    ```
To monitor the activity of the application you can 
  - Use `tail -f` on the log file from the node of interest, e.g., `tail -f server_logs/192.168.10.122` wiill tail the logs from the System Operator.
  - Watch the gui in the Node-Red Dashboard
  ![node-red-running](README_images/node-red-dashboard-running.PNG) 

### Interact with the application
Once the relays, generators, and battery inverters have values displayed in the GUI the application is ready for user inputs.
1. The first input is to click the `Energize` toggle. This sends a command to turn on the generators and inverters and will cause the values to change at the relays, generators, and battery inverters. The approximate P values in each state are shown in the table below.
1. The second input is to click the `SEND REGULATION UPDATE` button. This sets the target value for the power across PCC1 PCC2 and PCC3. 
1. Click the `Active Control` toggle. This causes the app to switch to active control and it will gradually update the values until the relays all have a P value of 400. 

|       | initial | Energized | Active Control | Islanded |
| ----  | ------- | --------- | -------------- | -------
| PCC1  | 2220    | 1440      | 400            | 0
| PCC2  | 1800    | 520       | 400            |
| PCC3  | 2000    | 2965      | 400            |
| F1108 | 0       | 0         | 0              |
| F2217 | 0       | 0         | 0              |
| Gen1  | 0.08    | 0.5       | 0.56           | 
| Gen2  | 0.05    | 0.5       | 0.38           | 
| Gen3  | 0.08    | 0.5       | 0.46           |
| C1    | -0.009  |           | 0.45           |
| C2    | -0.009  |           | 0.45           |
| C4    | -0.009  |           | 0.46           |
| C5    | -0.009  |           | 0.41           |
| C6    | -0.009  |           | 0.41           |


### Examples

Provide detailed examples of how to use different parts of your project. You can also include GIFs or images to demonstrate its features.


### Troubleshooting/FAQ

If the app is not behaving as expected here are some things to check.
* Log Files
  * **UNEXPECTED CONDITIONS** : Congratulations! You found an unanticipated combination of relay and fsm states that has not been handled. Please open a bug report. 

**FAQ**
* Q: The power across the relay is not regulated when toggling secondary control.
* A: One potential cause for this behavior is if there is no message exchange between the group members. This will  

## Contributing

Explain how others can contribute to your project. Include guidelines for bug reports, feature requests, and pull requests.

### Bug Reports

Explain how to submit bug reports, what information to include, and how issues will be tracked and resolved.

### Feature Requests

Explain how to submit feature requests and what information you need from contributors to evaluate and implement new features.

### Pull Requests

Explain the process for submitting pull requests, including any coding standards or conventions to follow. Mention any automated testing or CI/CD processes.

## License

Specify the license under which your project is distributed. Include a brief summary of the license terms or a link to the full license text.

## Acknowledgments

Thank any individuals, projects, or organizations that inspired or helped you during the development of your project. You can also mention any libraries, tools, or resources you used and provide links to their respective sources.

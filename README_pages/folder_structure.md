# Folder Structure
___
* `applibs`: Contains the IMCP control application code as well as some utility code.
  * `applicationPy.py`: Contains the distributed control application code for each of the microgrid states.
  * `ComputationalComponent.py`: Contains the RIAPS code inherited by the RIAPS  app DERs. It receives messages from the FSM,  the Relays, the other DERs and uses this information in conjuction with its own measurements to determine which control application to run.
  * `consensusPY.py`: Each of the distributed control applications use a consensus algorithm to determine the setpoints for that application. The consensus algorithms implemented are in this file.
  * `constants.py`: Contains the controller gains used by the IMCP control application. It also sets the default values for active and reactive power regulation; the default values are used unless the operator sends a message to the Power Manager (`GEN1_PWR_MANAGER.py`).
  * `helper.py`: Contains definitions for having colored text in the terminal. 
  * `log_preprocessor.py`: Provides a alternative to standard logging calls. It is used to log the data in a json format that is easier to parse after it is sent to the log aggregation server.
* `cfg_ncsu`/`cfg_vanderbilt`: These are the site specific configuration files.
  * `mqtt.yaml`: Provides the configuration for the MQTT device component to connect to the MQTT broker and includes the topics to subscribe to. We use mqtt to communicate with a node-red gui, the `riaps_to_mqtt_mapping` is used to map the device name used in these config files and the name used in the node-red gui.
  * `topology.yaml`: Provides topology information about the grid. Specifically it provides a name for each of the groups formed by the relay states. It also describes the `electrically_independent_groups` which are the groups that can be isolated from one another.  The `groups_connected_by_relay` uses the the indices from the `electrically_independent_groups` to describe which groups are connected by a given relay.
  * Device list files (e.g., in `cfg_ncsu` `DSP111-DeviceList.yaml` and `RELAYF1.yaml`). The `device_list` is a list of the names of the config files for each of the devices. The `device_list` is used by the RIAPS device component to determine which devices to control.
  * Device config files (e.g., in `cfg_ncsu` `DSP111.yaml` and `RELAYF1.yaml`). These files contain the configuration information for each of the devices.
* `DSP_Code`: This is the code that is loaded onto the DSPs that are used to simulate the inverters using the Code Complete software.
* `GUI`: This contains the node-red gui code.
* `imcp_fsm`: This contains the base FSM code for a riaps IMCP control application. The `states.yaml`, `transitions.yaml` and `model.py` define that state machine itself, its states, transitions and the implementation of the functions that are called before, during, and after a transition respectively. The `machines/riaps.py` file extends the pytransitions state class to be compatible with a RIAPS application. The `baseRiapsComponents/IMCP_FSM.py` is a RIAPS component that properly initialzes the FSM and should be inherited by the FSM in the RIAPS application.
* `log`: This contains a script for opening a terminals or tailing the logs from all the target nodes included in the deployment file.
* `server_logs`: This contains the logs from the log aggregation server.
* `tests`: This contains the tests for the IMCP control application.
* `transitions`: is a copy of the pytransitions version '0.9.0' package that was included as an application library to eliminate the need to install the package on target nodes.
* `utils`: This is redundant with the `applibs/helper.py` file in that it also defines colors for the terminal. Perhaps this should be included in RIAPS as a module. 
* RIAPS files:
  * `IMCP_Banshee_NCSU.riaps`: This is the RIAPS application file for the Banshee testbed.
  * `IMCP_SingleFeeder_VU.riaps`: This is the RIAPS application file for the single feeder testbed.
  * `IMCP_Banshee_NCSU.depl`: This is the RIAPS deployment file for the Banshee testbed at NCSU.
  * `IMCP_SingleFeeder_VU.depl`: This is the RIAPS deployment file for the single feeder testbed at Vanderbilt.
  * `IMCP_Banshee_NCSU_test.depl`: This is the RIAPS deployment file for the `test_mqtt_2_riaps_communication` test on the Banshee testbed at NCSU.
  * `riaps-log.conf`: This is the application log configuration file. 
* Application Implementation files:
  * `FSM.py`
  * `GEN1.py`
  * `GEN1_PWR_MANAGER.py`
  * `GROUP_MANAGER.py`
  * `MQTT.py`
  * `RELAYF1.py`
  * `RELAYF1_MANAGER.py`
  * `imcp.capnp`: This is the capnp file that defines the messages used by the application.
  * `SYSTEM_OPERATOR_*.py`
    * `BANSHEE`: This is the system operator for standalone demo at NCSU.
    * `MQTT`: This is the system operator for the Banshee testbed at NCSU that is driven by the node-red gui.
    * `SINGLE_FEEDER`: This is the system operator for the single feeder testbed at Vanderbilt that is driven by the node-red gui.

## Table of Contents
<!-- TOC -->
  * [Table of Contents](#table-of-contents)
  * [Devices](#devices)
    * [Device lists](#device-lists)
    * [Device configuration](#device-configuration)
      * [Modbus](#modbus)
  * [MQTT - `cfg_ncsu/mqtt.yaml`](#mqtt---cfgncsumqttyaml)
  * [Grid Topology - `cfg_ncsu/topology.yaml`](#grid-topology---cfgncsutopologyyaml)
  * [Distributed Controller Gains](#distributed-controller-gains)
<!-- TOC -->

## Devices

### Device lists
The device lists are files used to specify the path to the device configuration files and their names. As well as the global debug mode. 
The path to these files are passed in the riaps `.depl` files to RIAPS actors that have components that inherit from the ModbusDeviceComponent class.
For additional information on the ModbusDeviceComponent class and its usage and configuration see the [minimal example](https://github.com/RIAPS/interface.modbus.libs/tree/main/example/Minimal) in the [riaps.interfaces.modbus](https://github.com/RIAPS/interface.modbus.libs/tree/main) repository.
```yaml
path_to_config_files: ./cfg_ncsu
names:
  - <device_name> (e.g. 'F1_DSP111')
debugMode: True
```

### Device configuration
The device configuration files are comprised of the following 6 sections:
* Device Information
* Instance Information
* GROUP MANAGEMENT
* FSM
* MODBUS 
* MODBUS REGISTERS


#### Modbus
The device configuration files include a section to configure the modbus connection as well as the registers.
For additional information on the modbus configuration see the [minimal example](https://github.com/RIAPS/interface.modbus.libs/tree/main/example/Minimal) in the [riaps.interfaces.modbus](https://github.com/RIAPS/interface.modbus.libs/tree/main) repository.



## MQTT - `cfg_ncsu/mqtt.yaml`
The MQTT configuration file is used to configure the connection to the MQTT broker and the topics that the RIAPS application is subscribing to. 
In this application we are using a RIAPS MQTT device component to receive messages from the MQTT broker and publish them to the System Operator. These messages are then used to specify the desired states for the relays and the desired power setpoints for the generators. The source of the MQTT messages can either be an external script such as is done by the test in `tests/test_24_app.py::test_app` or from the `node-red` GUI. The identities used in the GUI for the SVG elements does not match the identifiers used in the Instance Information section of the device configuration files. The mapping between the two is done in the `cfg_ncsu/mqtt.yaml` file. The following is an example of the `cfg_ncsu/mqtt.yaml` file:
```yaml
broker_connect_config:
  host: 192.168.10.139  # the hostname or IP address of the remote broker
  port: 1883  # the network port of the server host to connect to. Defaults to 1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you are using tls_set() or tls_set_context(), the port may need providing manually
  keepalive: 60  # maximum period in seconds allowed between communications with the broker. If no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker
  bind_address: ""  # the IP address of a local network interface to bind this client to, assuming multiple interfaces exist
topics:
  subscriptions:
    - riaps/cmd
    - mg/request_scenario
    - mg/event
riaps_to_mqtt_mapping:
  # uid: Name in One-line diagram
  "201": "GEN1"
  "202": "GEN2"
  "203": "GEN3"
```


## Grid Topology - `cfg_ncsu/topology.yaml`
This file is used to capture certain aspects of the grid topology that are relevant to the application. `electrically_independent_groups` is an ordinal dictionary of the DERs that cannot be disconnected from one another, meaning there is no relay that can be opened to separate those DERs. `electrically_independent_group_names` is a dictionary where the keys are the values of the `electrically_independent_groups` dictionary and the values are names assigned to that group that are used by the app to construct names for the groups that are formed when closing relays. `groups_connected_by_relay` is a dictionary where the keys are the names of the relays in the topology and the keys are the ordinal numbers of the `electrically_independent_groups` that they connect. Finally, the `DIRECTLY_CONNECTED_RELAYS` are defined. This is a dictionary where the keys are the names of the PCC relays and the value is a list of the names of the relays that have a direct connection to that PCC relay. This is used by the DERs because we only want a DER control a relay if that relay cannot be isolated from the DER. The reason is that otherwise we have to concern ourselves with loops in the network and the need to compute the direction of the power flow.
```yaml
# Group membership configuration
electrically_independent_group_names: 
  "['grid1']": G1
  "['grid2']": G2
  "['grid3']": G3
  "['111', '112', '201']": F1
  "['114', '202']": F2
  "['115', '116', '203']": F3

electrically_independent_groups:
  0: ['grid1']
  1: ['grid2']
  2: ['grid3']
  3: ['111', '112', '201']
  4: ['114', '202']
  5: ['115', '116', '203']

# names the coordinates in an adjacency matrix according to the relay
# that causes the relevant electrically independent groups to be connected.
groups_connected_by_relay:
  'F1PCC': [0, 3]
  'F2PCC': [1, 4]
  'F3PCC': [2, 5]

  'F1108': [3, 4]
  'F1109': [3, 4]
  'F1111': [3, 4]
  'F1113': [3, 5]

  'F2213': [4, 5]
  'F2216': [4, 5]
  'F2217': [4, 5]

DIRECTLY_CONNECTED_RELAYS:
  F1PCC: ["F1PCC", "F1108", "F1109", "F1111", "F1113"]
  F2PCC: ["F2PCC", "F1108", "F1109", "F1111", "F2213", "F2216", "F2217"]
  F3PCC: ["F3PCC", "F1113", "F2213", "F2216", "F2217"]
```

## Distributed Controller Gains - `applibs/constants.py`
`applibs/constants.py` contains the default values for the controller gains. These values can be changed to tune the various controllers. The following table shows the default values for the controller gains.

|                            | ECONOMIC DISPATCH | VOLTAGE ESTIMATION | RESYNCHRONIZATION | RELAY OPEN           | RELAY CLOSE           | SECONDARY CONTROL |
|----------------------------|-------------------|--------------------|-------------------|----------------------|-----------------------|-------------------|
| app name                   | economicApp       | estimateApp        | resyncApp         | reconfigRelayOpenApp | reconfigRelayCloseApp | secondApp         |
| alpha_x_gain               | 0.8               |                    |                   |                      |                       |                   |
| edp_reactive_pwr_ctrl_gain | 100               |                    |                   |                      |                       |                   |
| eps_reg_gain               | 0.01*0.3          |                    |                   |                      |                       |                   |
| pcc_reactive_pwr_ctrl_gain | 0.5*0.3           |                    |                   |                      |                       |                   |
| consensus_gain             |                   | 0.25               |                   |                      |                       |                   |
| freq_ctrl_gain             |                   |                    | 15/3              |                      | 15/3                  | 15/3              |
| active_pwr_ctrl_gain       |                   |                    | 0.8*0.1           | 0.8*0.1              | 0.8*0.1               | 0.8*0.1           |
| reactive_pwr_ctrl_gain     |                   |                    | 200*0.1           | 200*0.1              | 200*0.1               | 200*0.1           |
| voltage_ctrl_gain_relay    |                   |                    | 0.2               |                      | 0.2                   |                   |
| voltage_ctrl_gain_island   |                   |                    |                   |                      |                       | 0.2 * 20 * 480    |
| relay_p_ctrl_gain          |                   |                    |                   | 0.0002               |                       |                   |
| relay_q_ctrl_gain          |                   |                    |                   | 0.05                 |                       |                   |


Description of the controller gains:
* **alpha_x_gain** is the first consensus gain for economic dispatch. It is the gain for the consenus error of the incremental cost.
* **edp_reactive_pwr_ctrl_gain** is the second consensus gain for economic dispatch. It is the gain for the consensus error of the reactive power.
* **eps_reg_gain** is the first pinning gain for economic dispatch. It is the gain for the error of the active power at the PCC.
* **pcc_reactive_pwr_ctrl_gain** is the second pinning gain for economic dispatch. It is the gain for the error of the reactive power at the PCC.
* **consensus_gain** is the gain for the consensus error of the estimated voltage.
* **freq_ctrl_gain** is the first pinning gain for resync, relay close, and secondary control. It is the gain for the error between the DERs frequency and the nominal frequency (60hz). 
* **active_pwr_ctrl_gain** is the first consensus gain. It is the gain for the consenus error of the active power of the DERs.
* **reactive_pwr_ctrl_gain** is the second consensus gain. It is the gain for the consenus error of the reactive power of the DERs.
* **voltage_ctrl_gain_relay** is the first pinning gain. It is the gain for the error of the voltage across the relay under control.
* **voltage_ctrl_gain_island** is a pinning gain. It is the gain for error between the average voltge of all connected DERs and the nominal voltage. Because the average and nominal voltage are in per unit form they are multiplied by 480 (the inverter voltage) to be comparable to the **voltage_ctrl_gain_relay**. It can also be considered to make it easier to compare generator voltage with inverter voltage. The 20 is approximately 13800/480.
Both the control gains should be roughly the same magnitude, but since the voltage magnitudes differ we add the terms explicitely to make them comparible. 
* **relay_p_ctrl_gain** is the first pinning gain. It is the gain of error between the active power flow through the relay and 0.
* **relay_q_ctrl_gain** is the second pinning gain. It is the gain of error between the reactive power flow through the relay and 0.
impact relay control speed. p controls active q controls reactive. May have to reduce for power-sharing.


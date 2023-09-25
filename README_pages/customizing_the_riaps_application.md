## Table of Contents
<!-- TOC -->
* [Modbus Devices](#modbus-devices)
* [MQTT](#mqtt)
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




## MQTT
`cfg_ncsu/mqtt.yaml`

## Grid Topology
`cfg_ncsu/topology.yaml`

## Distributed Controller Gains
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
* **alpha_x_gain** controls
* **edp_reactive_pwr_ctrl_gain** controls
* **eps_reg_gain** controls
* **pcc_reactive_pwr_ctrl_gain** controls
* **consensus_gain** controls
* **freq_ctrl_gain** controls
* **active_pwr_ctrl_gain** and **reactive_pwr_ctrl_gain** controls the balance between the active and reactive power.
* **voltage_ctrl_gain_relay** controls
* **voltage_ctrl_gain_island** is multiplied by 480 to make it easier to compare generator voltage with inverter voltage.
* **relay_p_ctrl_gain** and **relay_q_ctrl_gain** impact relay control speed. p controls active q controls reactive. May have to reduce for power-sharing.


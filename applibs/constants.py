# ---- POWER TRANSFER AT PCC RELAY ----
# relevant in grid-tied mode used in the ComputationalComponentAll.py
default_regulation_active_power = 400  # regulation active power
default_regulation_reactive_power = 300  # regulation reactive power


# ---- ECONOMIC DISPATCH CONTROL PARAMETERS ----
alpha_x_gain = 0.8  # EconomicDispatch
edp_reactive_pwr_ctrl_gain = 100  # EconomicDispatch
eps_reg_gain = 0.01*0.3  # EconomicDispatch
pcc_reactive_pwr_ctrl_gain = 0.5*0.3  # EconomicDispatch

# ---- VOLTAGE ESTIMATION CONTROL PARAMETERS ----
consensus_gain = 0.25  # VoltageEstimation

# ---- RESYNCHRONIZATION, RELAY OPEN/CLOSE, SECONDARY CONTROL PARAMETERS ----
freq_ctrl_gain = 15/3  # ResynchronizationControl/RelayCloseControl/SecondaryControl
# active and reactive power control gains control the balance between the active and reactive power(?).
# TODO: I don't know what these actually balance. Hao just said they are for balance.
active_pwr_ctrl_gain = 0.8*0.1  # ResynchronizationControl/RelayCloseControl/RelayOpenControl/SecondaryControl
reactive_pwr_ctrl_gain = 200*0.1  # ResynchronizationControl/RelayCloseControl/RelayOpenControl/SecondaryControl

voltage_ctrl_gain_relay = 0.2  # ResynchronizationControl/RelayCloseControl
voltage_ctrl_gain_island = 0.2*20*480  # SecondaryControl
# Multiply by 480 to make it easier to compare generator voltage with inverter voltage

# impact relay control speed. p controls active q controls reactive. May have to reduce for power-sharing.
relay_p_ctrl_gain = 0.0002  # RelayOpenControl
relay_q_ctrl_gain = 0.05  # RelayOpenControl

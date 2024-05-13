# Numpy module is imported as 'np'
# Scipy module is imported as 'sp'
Tfast = 300e-6
R=.1
L=3e-3

Resr=1.5
Cf=20e-6

Lgrid=4e-6
Rgrid=10e-3

Rline = 1e-3
Lline = 1e-6

config1 = {
    'port': 502,
    'ip_addr': '192.168.10.230',
    'netmask': '255.255.255.0',
    'slave_id': 17,
    'coil_input_addresses': '',
    'coil_output_addresses': '',
    'discrete_input_addresses': '',
    'holding_register_input_addresses': '',
    'holding_register_output_addresses': '',
    'input_register_adresses': '[0,1]f, \
                               [2,3]f, \
                               [4,5]f, \
                               [6,7]f, \
                               [8,9]f, \
                               [10,11]f, \
                               [12,13]f, \
                               [14,15]f, \
                               [16,17]f, \
                               [18,19]f, \
                               [20,21]f, \
                               [22,23]f, \
                               [24,25]f'
}
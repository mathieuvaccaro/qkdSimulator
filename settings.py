message_size = 250 # Number of bits for the QKD exchange
message_interval = 5 # Interval between each qubit (in ms)
tolerance_message_not_receive = 3 # How much time receiver wait before mark qubit as not received (/!\ This value need to be lower than message_interval !)


quantum_canal_noise = 0 # Noise on quantum canal in %

qber_percent = 20 # percent of qubits used for qber calculus
qber_tolerance = 11 # Tolerance of qber coeff (default : 11 for BB84 proptoocl)



eve_present = False
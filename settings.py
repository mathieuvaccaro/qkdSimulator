message_size = 3000 # Number of bits for the QKD exchange
message_interval = 2 # Interval between each qubit (in ms)
tolerance_message_not_receive = 0.7 # How much time receiver wait before mark qubit as not received (/!\ This value need to be lower than message_interval !)


quantum_canal_bit_loss = 5 # Noise on quantum canal in %
quantum_canal_bit_flip = 5

qber_percent = 20 # percent of qubits used for qber calculus
qber_tolerance = 11 # Tolerance of qber coeff (default : 11 for BB84 proptoocl)

protocol = "bb84" # for now only bb84 is compatible

eve_present = True

progress_bar = True
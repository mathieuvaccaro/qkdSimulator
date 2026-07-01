message_size = 10 # Number of bits for the QKD exchange
message_interval = 200 # Interval between each qubit (in ms)
tolerance_message_not_receive = 80 # How much time receiver wait before mark qubit as not received (/!\ This value need to be lower than message_interval !)


quantum_canal_noise = 0 # Noise on quantum canal in %
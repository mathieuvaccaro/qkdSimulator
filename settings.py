message_size = 1000 # Number of bits for the QKD exchange
message_interval = 3 # Interval between each qubit (in ms) (minimum 3ms)
tolerance_message_not_receive = 0.7 # How much time receiver wait before mark qubit as not received (/!\ This value need to be lower than message_interval !)

average_emitted_photon = 1 # Average number of emitted photon, in a perfect system, this value is 1. but it may be lower of higher (it's dangerous if higher) (poisson law)
# if -1, always emit 1 photon

quantum_canal_bit_loss = 2 # Noise on quantum canal (in %)
quantum_canal_bit_flip = 2

qber_percent = 20 # percent of qubits used for qber calculus
qber_tolerance = 11 # Tolerance of qber coeff (default : 11 for BB84 proptoocl)

protocol = "bb84" # for now only bb84 is compatible

progress_bar = True


#   _   _   _             _        
#  /_\ | |_| |_ __ _  ___| | _____ 
# //_\\| __| __/ _` |/ __| |/ / __|
#/  _  \ |_| || (_| | (__|   <\__ \
#\_/ \_/\__|\__\__,_|\___|_|\_\___/
                                  

# Mettre un flag d'attaque à True pour l'activer (une seule à la fois).
# Eve n'est présente sur le canal que si une attaque est active.
# Pour ajouter une nouvelle attaque : créer une sous-classe de Intercept,
# l'enregistrer dans attacks/attack_manager.py, puis ajouter son flag ici.
intercept_and_resent = True
PNS = False # Photon number splitting
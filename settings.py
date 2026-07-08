
#   _____ _       _           _ 
#  / ____| |     | |         | |
# | |  __| | ___ | |__   __ _| |
# | | |_ | |/ _ \| '_ \ / _` | |
# | |__| | | (_) | |_) | (_| | |
#  \_____|_|\___/|_.__/ \__,_|_|
message_size = 1000 # Number of bits for the QKD exchange                               
message_interval = 5 # Interval between each qubit (in ms) (minimum 3ms)
protocol = "bb84" # for now only bb84 is compatible

#   _____                _           
#  / ____|              | |          
# | (___   ___ _ __   __| | ___ _ __ 
#  \___ \ / _ \ '_ \ / _` |/ _ \ '__|
#  ____) |  __/ | | | (_| |  __/ |   
# |_____/ \___|_| |_|\__,_|\___|_|   
average_emitted_photon = 3 # Average number of emitted photon, in a perfect system, this value is 1. but it may be lower of higher (it's dangerous if higher) (poisson law)
# if -1, always emit 1 photon                                   
                                    

#   _____                  _    _                     
#  / ____|                | |  | |                    
# | |     __ _ _ __   __ _| |  | | ___  ___  ___  ___ 
# | |    / _` | '_ \ / _` | |  | |/ _ \/ __|/ _ \/ __|
# | |___| (_| | | | | (_| | |  | | (_) \__ \  __/\__ \
#  \_____\__,_|_| |_|\__,_|_|  |_|\___/|___/\___||___/
quantum_canal_bit_loss = 2 # Noise on quantum canal (in %)
quantum_canal_bit_flip = 3 # Add x/2 % of qber (for bb84 ofc)                                                   

#  _____               _                            ____  _               
# |  __ \             (_)                  ___     / __ \| |              
# | |__) |___  ___ ___ ___   _____ _ __   ( _ )   | |  | | |__   ___ _ __ 
# |  _  // _ \/ __/ _ \ \ \ / / _ \ '__|  / _ \/\ | |  | | '_ \ / _ \ '__|
# | | \ \  __/ (_|  __/ |\ V /  __/ |    | (_>  < | |__| | |_) |  __/ |   
# |_|  \_\___|\___\___|_| \_/ \___|_|     \___/\/  \___\_\_.__/ \___|_|   
tolerance_message_not_receive = 3 # How much time receiver wait before mark qubit as not received (/!\ This value need to be lower than message_interval !)
qber_percent = 20 # percent of qubits used for qber calculus
qber_tolerance = 11 # Tolerance of qber coeff (default : 11 for BB84 proptoocl)                                                               
                                                                         
#           _____  _____      
#     /\   |  __ \|  __ \     
#    /  \  | |__) | |  | |___ 
#   / /\ \ |  ___/| |  | / __|
#  / ____ \| |    | |__| \__ \
# /_/    \_\_|    |_____/|___/
perfect_apd = False # Is apds use is perfect ? (overwrite follows values)
breakdown_voltage = 7 # def : 7
dead_time = 300 #def : 300
bias_voltage = 5 #def : 5
gate_off_duration = 20 #def : 20
gate_on_duration = 20 #def : 20

#          _   _             _        
#     /\  | | | |           | |       
#    /  \ | |_| |_ __ _  ___| | _____ 
#   / /\ \| __| __/ _` |/ __| |/ / __|
#  / ____ \ |_| || (_| | (__|   <\__ \
# /_/    \_\__|\__\__,_|\___|_|\_\___/                       

# Mettre un flag d'attaque à True pour l'activer (une seule à la fois).
# Eve n'est présente sur le canal que si une attaque est active.
# Certaines attaques sont simulés réalistiquement (exemple PNS) tandis que d'autre sont simulés hypotétiquement (trojan horse). Les attaques simulés de manière réaliste ont un commentaire X a coté
intercept_and_resent = False # X
PNS = False                  # X
TrojanHorse = True

#     /\                                   
#    /  \   _ __  _ __   _____  _____  ___ 
#   / /\ \ | '_ \| '_ \ / _ \ \/ / _ \/ __|
#  / ____ \| | | | | | |  __/>  <  __/\__ \
# /_/    \_\_| |_|_| |_|\___/_/\_\___||___/
progress_bar = True
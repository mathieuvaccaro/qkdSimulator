r"""
   _____ _       _           _ 
  / ____| |     | |         | |
 | |  __| | ___ | |__   __ _| |
 | | |_ | |/ _ \| '_ \ / _` | |
 | |__| | | (_) | |_) | (_| | |
  \_____|_|\___/|_.__/ \__,_|_|
"""
# Les paramètres globaux sotn aussi atifs pour les tests !
message_size = 500 # Nombre de qubit échangé au total                              
message_interval = 4 # Intervale en ms entre chaque qubit échange (par défaut 4ms) [mettre uen valeur inféireur peut introduire des erreurs !]
protocol = "bb84" # Protocole (pour l'instnat seulemetn bb84 est compatible)

r"""
   _____                _           
  / ____|              | |          
 | (___   ___ _ __   __| | ___ _ __ 
  \___ \ / _ \ '_ \ / _` |/ _ \ '__|
  ____) |  __/ | | | (_| |  __/ |   
 |_____/ \___|_| |_|\__,_|\___|_|   
"""
 
average_emitted_photon = -1 # Nombre de moyen de photon émis par le sender (suit une loi de poisson). -1 = toujours 1 photon (désactive PNS !)
                                    
r"""
   _____                  _    _                     
  / ____|                | |  | |                    
 | |     __ _ _ __   __ _| |  | | ___  ___  ___  ___ 
 | |    / _` | '_ \ / _` | |  | |/ _ \/ __|/ _ \/ __|
 | |___| (_| | | | | (_| | |  | | (_) \__ \  __/\__ \
  \_____\__,_|_| |_|\__,_|_|  |_|\___/|___/\___||___/
"""
#La somme ne doit pas dépasser 100 (Remaruqe, les pourcentage sont cumulés (si il y a 50% de bit loss et 50% de bit flip tous les bits transmis seront faussé !))"""
# Possible de mettre au plus deux décimal
quantum_canal_bit_loss = 0.00
quantum_canal_bit_flip = 0.00                                                  

r"""
  _____               _                            ____  _               
 |  __ \             (_)                  ___     / __ \| |              
 | |__) |___  ___ ___ ___   _____ _ __   ( _ )   | |  | | |__   ___ _ __ 
 |  _  // _ \/ __/ _ \ \ \ / / _ \ '__|  / _ \/\ | |  | | '_ \ / _ \ '__|
 | | \ \  __/ (_|  __/ |\ V /  __/ |    | (_>  < | |__| | |_) |  __/ |   
 |_|  \_\___|\___\___|_| \_/ \___|_|     \___/\/  \___\_\_.__/ \___|_|   
"""

tolerance_message_not_receive = message_interval-0.2 # Temps en ms a attendre avant de déclarer le qubit perdu (il ne faut pas que cette valeur soit supérieur à message_interval !)
qber_percent = 20 # Part en % des bits siftés utilisés pour le calcul du qber
qber_tolerance = 11 # Tolérance du qber (par défaut 11% pour BB84)                                                         

r"""                                                                      
           _____  _____      
     /\   |  __ \|  __ \     
    /  \  | |__) | |  | |___ 
   / /\ \ |  ___/| |  | / __|
  / ____ \| |    | |__| \__ \
 /_/    \_\_|    |_____/|___/
"""
perfect_apd_bob = False # Mettre un apd parfait (écrase les valeurs suivante)
perfect_apd_eve = False
breakdown_voltage = 7 # def : 7
dead_time_min = 2 #def : 2 (en ms)
dead_time_max = 6 # def : 6
bias_voltage = 5 #def : 5
gate_off_duration = message_interval/2 #def : message_interval/2
gate_on_duration = message_interval/2 #def : message_interval/2
many_clicks_gestion = "THROWS" # Gestion des double click ("THROWS" -> Tous les bits sont jeté, "RANDOM" -> Le bit est choisi au hasard)

r"""
          _   _             _        
     /\  | | | |           | |       
    /  \ | |_| |_ __ _  ___| | _____ 
   / /\ \| __| __/ _` |/ __| |/ / __|
  / ____ \ |_| || (_| | (__|   <\__ \
 /_/    \_\__|\__\__,_|\___|_|\_\___/                       
"""
 
# Mettre un flag d'attaque à True pour l'activer (une seule à la fois).
# Eve n'est présente sur le canal que si une attaque est active.
# Certaines attaques sont simulés réalistiquement (exemple PNS) tandis que d'autre sont simulés hypotétiquement (trojan horse). Les attaques simulés de manière réaliste ont un commentaire X a coté
intercept_and_resent = False # X

PNS = False                  # X

TrojanHorse = False

DoubleClickEvent = False      # X
emission_click_event = 10

r"""
     /\                                   
    /  \   _ __  _ __   _____  _____  ___
   / /\ \ | '_ \| '_ \ / _ \ \/ / _ \/ __|
  / ____ \| | | | | | |  __/>  <  __/\__ \
 /_/    \_\_| |_|_| |_|\___/_/\_\___||___/
"""
    
# Vraiment juste esthetique
progress_bar = True
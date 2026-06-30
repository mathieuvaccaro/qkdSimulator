import os

import qutip
import numpy as np
import matplotlib.pyplot as plt
from random import randint as rng
from random import sample as rng_s

from utils.colors import bcolors

#__     __    _                 
#\ \   / /_ _| |_   _  ___  ___ 
# \ \ / / _` | | | | |/ _ \/ __|
#  \ V / (_| | | |_| |  __/\__ \
#   \_/ \__,_|_|\__,_|\___||___/

# Rect states
H = qutip.basis(2, 0) # Horizontal
V = qutip.basis(2, 1) # Vertical

# Diag sates (45 et -45°)
D = ((H+V) / np.sqrt(2)).unit() 
DM = ((H-V) / np.sqrt(2)).unit()

# Get state by bit and basis
STATES = {
    (0, 0): H,    # bit 0, rectiligne
    (1, 0): V,    # bit 1, rectiligne
    (0, 1): D,    # bit 0, diagonale
    (1, 1): DM,   # bit 1, diagonale   (ton |A>)
}

alice_bases = []
bob_bases = []
alice_bits = []
bob_bits = []

#  ___        ____       _   _   _                 
# / _ \      / ___|  ___| |_| |_(_)_ __   __ _ ___ 
#| | | |     \___ \ / _ \ __| __| | '_ \ / _` / __|
#| |_| |      ___) |  __/ |_| |_| | | | | (_| \__ \
# \___(_)    |____/ \___|\__|\__|_|_| |_|\__, |___/
#                                        |___/     
NOISED_CANAL = 0 # percetage of noise on public channel (0 -> No noise)
BITS_NUMBER = 10000 # Number of sended bits by alice
QBER_PERCENT = 20 # Percent of bits will be sacrified for qber calcul. percent of sifting bits
QBER_TOLERANCE = 11 # percent of tolerance


EVE_PRESENT = False # Is eve present ? . This variable is prerequise for next variables
# Attacks
ATTACK_INTERCEPT_AND_RESENT_CLASSICAL = True

# _        _    _ _                                    _ 
#/ |      / \  | (_) ___ ___        ___  ___ _ __   __| |
#| |     / _ \ | | |/ __/ _ \      / __|/ _ \ '_ \ / _` |
#| |_   / ___ \| | | (_|  __/      \__ \  __/ | | | (_| |
#|_(_) /_/   \_\_|_|\___\___|      |___/\___|_| |_|\__,_|
# Alice chose randomly a bit and a basis and send it to public channel
def Alice():
    # First, alice chose a random bit and a random basis
    sended_bit = rng(0, 1)
    alice_basis = rng(0, 1)
    sended_state = STATES[sended_bit, alice_basis]
    alice_bases.append(alice_basis)
    alice_bits.append(sended_bit)

    return sended_state

# ____          ____                  _ 
#|___ \        / ___|__ _ _ __   __ _| |
#  __) |      | |   / _` | '_ \ / _` | |
# / __/ _     | |__| (_| | | | | (_| | |
#|_____(_)     \____\__,_|_| |_|\__,_|_|
# Noise can be in canal.
# This program is linear, so bob can synchronize with Alice by time
def Canal(sended_state):
    if(NOISED_CANAL):
        print("Not yet implemented")
    else:
        return sended_state

# _____         _____           
#|___ /        | ____|_   _____ 
#  |_ \        |  _| \ \ / / _ \
# ___) |       | |___ \ V /  __/
#|____(_)      |_____| \_/ \___|
# Eve may be an intercept and resent attack
def Eve(sended_state):
    if(EVE_PRESENT):
        if(ATTACK_INTERCEPT_AND_RESENT_CLASSICAL):
            eve_basis = rng(0, 1)
            eve_basis_x = STATES[0, eve_basis]
            eve_basis_y = STATES[1, eve_basis]
            received_bit = qutip.measurement.measure(sended_state, [qutip.ket2dm(eve_basis_x), qutip.ket2dm(eve_basis_y)])[0]
            return STATES[received_bit, eve_basis]
    
    return sended_state

# _  _           ____        _     
#| || |         | __ )  ___ | |__  
#| || |_        |  _ \ / _ \| '_ \ 
#|__   _|       | |_) | (_) | |_) |
#   |_|(_)      |____/ \___/|_.__/ 
def Bob(sended_state):
    # First, alice chose a random bit and a random basis
    bob_basis = rng(0, 1)
    bob_bases.append(bob_basis)

    bob_basis_x = STATES[0, bob_basis]
    bob_basis_y = STATES[1, bob_basis]

    received_bit = qutip.measurement.measure(sended_state, [qutip.ket2dm(bob_basis_x), qutip.ket2dm(bob_basis_y)])[0]
    bob_bits.append(received_bit)

# ____        ____  _  __ _   _             
#| ___|      / ___|(_)/ _| |_(_)_ __   __ _ 
#|___ \      \___ \| | |_| __| | '_ \ / _` |
# ___) |      ___) | |  _| |_| | | | | (_| |
#|____(_)    |____/|_|_|  \__|_|_| |_|\__, |
#                                     |___/ 
# During sifting step, we check bases uses by alice and bob. If basis is equivalent we keep bit associate. However, if it isn't we
# throw away.
# bits_list is alice_bits and bob_list. Function will be called twice because during a real communication sifitng is done by Alice AND Bob
def Sifting(sended_bases, received_bases, bits_list):
    liste = []
    for i in range(min(len(sended_bases), len(received_bases))):
        if(sended_bases[i] == received_bases[i]):
            liste.append(bits_list[i])
    return liste

#  __          ___  ____  _____ ____     ____      _            _ 
# / /_        / _ \| __ )| ____|  _ \   / ___|__ _| | ___ _   _| |
#| '_ \      | | | |  _ \|  _| | |_) | | |   / _` | |/ __| | | | |
#| (_) |     | |_| | |_) | |___|  _ <  | |__| (_| | | (__| |_| | |
# \___(_)     \__\_\____/|_____|_| \_\  \____\__,_|_|\___|\__,_|_|
# Here, we suppose sended_bits and received_bits is only similar bits (no bits was lost during communication) so sended_bits and 
# received_bits are same len
def QBER(sended_bits, received_bits):
    nb_qber = int(QBER_PERCENT / 100 * len(sended_bits))
    random_indexes = rng_s(range(0, len(sended_bits)), nb_qber)
    qber_score = 0
    for idx in random_indexes:
        if sended_bits[idx] != received_bits[idx]:  # on incrémente si les bits diffèrent
            qber_score += 1
    return qber_score / nb_qber * 100  # taux en %

#  ____                 _           _             
# / ___|___  _ __   ___| |_   _ ___(_) ___  _ __  
#| |   / _ \| '_ \ / __| | | | / __| |/ _ \| '_ \ 
#| |__| (_) | | | | (__| | |_| \__ \ | (_) | | | |
# \____\___/|_| |_|\___|_|\__,_|___/_|\___/|_| |_|                       
def Conclusion(qber_score):
    os.system('cls' if os.name == 'nt' else 'clear')
    header = """
     ____       _        _ _              __                                 
    |  _ \  ___| |_ __ _(_) |___    ___  / _|                                
    | | | |/ _ \ __/ _` | | / __|  / _ \| |_                                 
    | |_| |  __/ || (_| | | \__ \ | (_) |  _|                                
    |____/ \___|\__\__,_|_|_|___/  \___/|_|   _           _   _             
     ___ ___  _ __ ___  _ __ ___  _   _ _ __ (_) ___ __ _| |_(_) ___  _ __  
    / __/ _ \| '_ ` _ \| '_ ` _ \| | | | '_ \| |/ __/ _` | __| |/ _ \| '_ \ 
   | (_| (_) | | | | | | | | | | | |_| | | | | | (_| (_| | |_| | (_) | | | |
    \___\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|_|\___\__,_|\__|_|\___/|_| |_|
    """

    print(bcolors.WARNING + header)
    print(bcolors.OKBLUE + f"Sending bits : {len(alice_bits)}")
    print(bcolors.OKBLUE + f"Sifted bits : {len(alice_sifted_bits)}")
    print(bcolors.OKBLUE + f"Difference : {len(alice_sifted_bits) / len(alice_bits) * 100:.2f}%")
    print("")
    if qber_score > QBER_TOLERANCE:
        print(bcolors.FAIL + f"QBER Score : {qber_score:.2f}")
        print(bcolors.FAIL + f"Communication was aborted !")
    else:
        print(bcolors.OKGREEN + f"QBER Score : {qber_score:.2f}")
        print(bcolors.OKGREEN + f"Communication was secured !")


# ____                    _             
#|  _ \ _   _ _ __  _ __ (_)_ __   __ _ 
#| |_) | | | | '_ \| '_ \| | '_ \ / _` |
#|  _ <| |_| | | | | | | | | | | | (_| |
#|_| \_\\__,_|_| |_|_| |_|_|_| |_|\__, |
#                                 |___/ 
n = 0
while(True):
    alice_bases = []
    bob_bases = []
    alice_bits = []
    bob_bits = []

    for i in range(BITS_NUMBER):
        alice_state = Alice()
        sended_state = Canal(alice_state)
        eve_state = Eve(sended_state)
        Bob(eve_state)

    alice_sifted_bits = Sifting(alice_bases, bob_bases, alice_bits)
    bob_sifted_bits = Sifting(alice_bases, bob_bases, bob_bits)
    qber_score = QBER(alice_sifted_bits, bob_sifted_bits)
    Conclusion(qber_score)
    print(n)
    n+=1


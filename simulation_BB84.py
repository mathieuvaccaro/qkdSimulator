from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

import random

N = 100

base_possible = ["rectiligne", "diagonal"]

base_emission = []
base_reception = []

bits_emis = []
bits_recus = []

bits_valables = [] # /!\ on ne garde seulement les index des bits avec la meme base !

bits_apres_qber_reception = []

qber_limit = 11 # En pourcentage, le score de qber limite
qber_percent = 0.10 # Parmis la liste des bits valable, qber est le pourcentage utilisé pour le calcul du qber
qber_score = 0

# Hadamard door : Convertir la base (rectiligne to diagnoal)
# 

#------------------------------------------------

# Création de N photons
# QuantumCircuit(Nmoibre de qubit, nombre de bits classqiue [pour le mesurer])
# Dans notre cas, on va utiliser qu'un seul qubit a chaque fois (je crois)

for i in range(N):

    #-------------------------------------------------------------
    # ALICE envoie
    #-------------------------------------------------------------


    # Création du qubit
    qc = QuantumCircuit(1, 1)

    # Assignation d'une valeur random
    bit = random.randint(0,1)
    if bit == 1:
        qc.x(0)
    bits_emis.append(bit)
    # Assignation d'une base random
    base_emission.append(base_possible[random.randint(0, len(base_possible)-1)])
    
    if base_emission[i] == "diagonal":
        qc.h(0)


    #-------------------------------------------------------------
    # Simulation d'envoie de bit (bruit canal)
    #-------------------------------------------------------------


    #-------------------------------------------------------------
    # Eve
    #-------------------------------------------------------------


    #-------------------------------------------------------------
    # BOB recoit
    #-------------------------------------------------------------

    base_reception.append(base_possible[random.randint(0, len(base_possible)-1)])
    if base_reception[i] == "diagonal":
        qc.h(0)
    
    # On mesure le photon et donc le fige
    qc.measure(0, 0)

    
    sim = AerSimulator()
    result = sim.run(qc, shots=1).result().get_counts()
    bit_received = int(max(result.keys()))  # Extraire le bit mesuré
    bits_recus.append(bit_received)



#-------------------------------------------------------------
# Sifting (Public)
#-------------------------------------------------------------
for i in range(N):
    if(base_emission[i] == base_reception[i]):
        bits_valables.append(i)


#-------------------------------------------------------------
# Calcul QBER
#-------------------------------------------------------------
# On va copier bits valable vers bits après qber pour être sur de garder les bits garder avant le qber (juste pour les stats)
# L'idée est de prendre qber_percent % des bits ayant la meme base, de checker les bits, si c'est les meme on fait +0 sinon +1
bits_apres_qber = bits_valables.copy()
nb_bits_for_qber = round(qber_percent * len(bits_apres_qber))
for i in range(nb_bits_for_qber):
    random_index = random.randint(0, len(bits_apres_qber)-1)
    index_original = bits_apres_qber[random_index]
    qber_score = qber_score if  bits_emis[index_original] == bits_recus[index_original] else qber_score +1 # Si meme bits alors +0 sinon +1

    del bits_apres_qber[random_index]

# On divise pour regarder le ratio, puis x100 poura voir en pourcante
qber_score = (qber_score / nb_bits_for_qber) * 100

#-------------------------------------------------------------
# Compte rendu
#-------------------------------------------------------------
print(f"Résultats :")
print(f"*"*30)
print(f"TRASNFEREn : ")
print(f"Bits émise : {bits_emis}")
print(f"Bits recus : {bits_recus}")
print(f"")
print(f"Bases émises : {base_emission}")
print(f"Bases recus : {base_reception}")
print(f"*"*30)
print(f"SIFTING : ")
print(f"Quantité de bits gardés après sifting : {len(bits_valables)} ({len(bits_valables)/len(bits_emis)*100}%)")
print(f"*"*30)
print(f"QBER : ")
print(f"Quantité de bits sacrifié pour le QBER : {nb_bits_for_qber}")
print(f"Score qber : {qber_score}")
print(f"*"*30)
print(f"CONCLUSION : ")
if(qber_score <= qber_limit):
    print("La communication est sécurisé !")
    cle = [bits_recus[i] for i in bits_apres_qber]
    print(f"La clé est : {cle}")
else:
    print("/!\\ La communication n'est pas sécurisé !")
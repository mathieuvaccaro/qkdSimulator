import components.clock as clock
import components.sender as sender
from components.quantum_canal import QuantumCanal # idk why i have to import only class and not file -_-
import components.receiver as receiver
import components.apd as apd
import settings
import components.sifting as sifting
from utils.colors import bcolors
import components.qber as qber
from utils.percent_corrupted_key import how_much_key_corrupted
from attacks.attack_manager import get_active_attack


import os
import sys

def restart():
    """Oublie tout : remplace le processus par une instance neuve du script."""
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable] + sys.argv)

"""
Le simulateur fonctionne grâce a une clock global. Dans un cas réel il faudrait utilisé deux clocks distinctes synchronisé, mais bon personne n'est parfait....
"""

def init_communication():
    """Le point de départ du projet"""

    print("Initialisation en cours...")
    # Creating channel
    quantum_canal = QuantumCanal()
    
    # Alice et Bob utilisent une clock commune, ici elle est dans le manager.py, mais l'idée finale est de la faire communiquer grâce a un canal publique
    commune_clk = clock.Clock(settings.message_interval)

    # APDs
    if(settings.perfect_apd):
        apd0 = apd.Apd(0, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0)
        apd1 = apd.Apd(1, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0)
    else:
        apd0 = apd.Apd(
                    linked_bit=0, 
                    clock_period=settings.message_interval, 
                    gate_off_duration=settings.gate_off_duration, 
                    gate_on_duration=settings.gate_on_duration, 
                    dead_time=settings.dead_time
                    )
        
        apd1 = apd.Apd(
                    linked_bit=1, 
                    clock_period=settings.message_interval, 
                    gate_off_duration=settings.gate_off_duration, 
                    gate_on_duration=settings.gate_on_duration, 
                    dead_time=settings.dead_time
                    )
        
    # Création des entités
    Alice = sender.Sender(quantum_canal, commune_clk)
    Bob = receiver.Receiver(apd0, apd1, quantum_canal, commune_clk)

    # Canal de communication
    quantum_canal.setSender(Alice)
    quantum_canal.setReceiver(Bob)

    # Assign Bob to apd
    apd0.set_parent(Bob)
    apd1.set_parent(Bob)
    commune_clk.subscribe(Bob.prepare_bases)
    commune_clk.subscribe(Alice.emit_qubit)
    commune_clk.subscribe(Bob.detect_lost_qubit)

    # Select attack
    AttackClass = get_active_attack()
    eve_active = AttackClass is not None

    if(eve_active):
        if(settings.perfect_apd):
            apdEve0 = apd.Apd(0, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0) # For now we create perfect apd
            apdEve1 = apd.Apd(1, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0)
        else:
            apdEve0 = apd.Apd(0, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0) # For now we create perfect apd
            apdEve1 = apd.Apd(1, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0)
        Eve = AttackClass(apdEve0, apdEve1, quantum_canal, commune_clk, Alice, Bob)

        quantum_canal.setInterceptor(Eve)
        apdEve0.set_parent(Eve)
        apdEve1.set_parent(Eve)
        apdEve0.run()
        apdEve1.run()
        apdEve0.start_clock()
        apdEve1.start_clock()


    print("Initialisation terminé !")

    print("Lancement ...")
    apd0.run()
    apd1.run()

    apd0.start_clock()
    apd1.start_clock()
    commune_clk.start()

    # Les deux fonctions sont bloquante, et seront débloqués lorsque alice fini ses envoie de message et que bob finissent la réception
    Alice.communication_finished.wait()
    Bob.communication_finished.wait()

    # Bob clôt la communication depuis un callback -> il stoppe la clock DEPUIS le
    # thread de la clock, donc sans join. Or, sur ce dernier tick, le callback
    # detect_lost_qubit d'Eve peut encore être en train de dormir (tolerance) et
    # n'a pas encore enregistré sa base/son bit. On rejoint donc explicitement le
    # thread de la clock depuis le thread principal pour garantir que TOUS les
    # callbacks du dernier tick (Eve comprise) sont terminés avant le sifting.
    #commune_clk.stop()

    # Bob annonce publiquement les slots où il n'a PAS eu de détection valide
    # (perte sur le canal, photon jeté par un APD imparfait, ou détection en
    # retard) en mettant leur base à -1. Ainsi le sifting d'Alice ET de Bob
    # exclut exactement les mêmes slots -> clés alignées, aucun -1 ne fuite.
    for i in range(len(Bob.chosen_bases)):
        if Bob.measured_bits[i] == -1:
            Bob.chosen_bases[i] = -1
    print(f"AAAAA {Alice.sent_bits}")
    print(f"BOBBOB {Bob.measured_bits}")
    keyAlice = sifting.sifting(Alice, Bob.chosen_bases) # For now, we don't simulate alice and bob basis communication (because is on public channel)
    keyBob = sifting.sifting(Bob, Alice.chosen_bases)
    if(len(keyAlice) == 0 or len(keyBob) == 0):
        raise Exception(f"La clé d'alice et/ou de bob est vide ({len(keyAlice)}, {len(keyBob)})")

    if(len(keyAlice) != len(keyBob)):
        print(bcolors.FAIL + f"[ERROR] Alice and bob haven't same keys size ! ({len(keyAlice)} vs {len(keyBob)})" + bcolors.ENDC)
    elif(keyAlice != keyBob):
        print(bcolors.WARNING + f"[WARN] Alice and bob haven't same keys (taille = {len(keyAlice)} et ({how_much_key_corrupted(keyAlice, keyBob)}%)" + bcolors.ENDC)
    else:
        print(bcolors.OKGREEN + f"[GOOD] Alice and bob have same keys (taille de la clé : {len(keyAlice)}!"+ bcolors.ENDC)
    (qber_value, final_key) = qber.qber_calculus(keyAlice, keyBob)



    if(qber_value < settings.qber_tolerance):
        print(bcolors.OKGREEN + f"[GOOD] Alice and Bob have a good qber value ({qber_value})%" + bcolors.ENDC)
    else:
        print(bcolors.FAIL + f"Qber is very high : {qber_value}. Communication aborting ..."+ bcolors.ENDC)

    if(eve_active):
        # Eve exploite les bases d'Alice, publiques une fois la communication finie
        Eve.resolve_knowledge(Alice.chosen_bases)
        keyEve = sifting.eve_sifting(Eve, Alice.chosen_bases, Bob.chosen_bases)
        if(len(keyEve) != len(keyAlice)):
            print(bcolors.WARNING + f"Alice and Eve size's key aren't same :" + bcolors.ENDC)
        print(bcolors.FAIL + f"Eve got {how_much_key_corrupted(final_key, keyEve)} % of Alice key")

while(True):
    init_communication()
    restart()

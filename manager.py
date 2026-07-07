import components.clock as clock
import components.sender as sender
from components.quantum_canal import QuantumCanal # idk why i have to import only class and not file -_-
import components.receiver as receiver
import components.apd as apd
import settings
import threading
import components.sifting as sifting
from utils.colors import bcolors
import components.qber as qber
from utils.percent_corrupted_key import how_much_key_corrupted
from attacks.attack_manager import get_active_attack

def init_communication():
    print("Initialisation en cours...")
    # Creating channel
    quantum_canal = QuantumCanal()
    
    # Creating and linked with globa clock
    commune_clk = clock.Clock(settings.message_interval) # We actually linked in by manager, but the idea is linked clock with public_canal.py !

    # Creating apd
    apd0 = apd.Apd(0, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0) # For now we create perfect apd
    apd1 = apd.Apd(1, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0)
    
    # Creating entities
    Alice = sender.Sender(quantum_canal, commune_clk)
    Bob = receiver.Receiver(apd0, apd1, quantum_canal, commune_clk) # And linked with apd

    # Assign canal ALice and bob
    quantum_canal.setSender(Alice)
    quantum_canal.setReceiver(Bob)

    # Assign Bob to apd (j'pense il y a une bien meilleur faonc de faire)
    apd0.set_parent(Bob)
    apd1.set_parent(Bob)


    # An attack is active only if one of its flags is set in settings.py.
    # The registry (attacks/attack_manager.py) tells us which Intercept subclass
    # to instantiate; Eve is present on the channel only when an attack is active.
    AttackClass = get_active_attack()
    eve_active = AttackClass is not None

    if(eve_active):
        apdEve0 = apd.Apd(0, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0) # For now we create perfect apd
        apdEve1 = apd.Apd(1, clock_period=settings.message_interval, gate_off_duration=0, gate_on_duration=1000, dead_time=0)
        Eve = AttackClass(apdEve0, apdEve1, quantum_canal, commune_clk)

        quantum_canal.setInterceptor(Eve)
        apdEve0.set_parent(Eve)
        apdEve1.set_parent(Eve)
        thread_apdEve0 = threading.Thread(target=apdEve0.detect_photon)
        thread_apdEve1 = threading.Thread(target=apdEve1.detect_photon)

        thread_apdEve0.start()
        thread_apdEve1.start() 
        apdEve0.run()
        apdEve1.run()
        apdEve0.start_clock()
        apdEve1.start_clock()


    print("Initialisation terminé !")

    print("Lancement ...")
    apd0.run()
    apd1.run()


    thread_apd0 = threading.Thread(target=apd0.detect_photon)
    thread_apd0.start()
    thread_apd1 = threading.Thread(target=apd1.detect_photon)
    thread_apd1.start()
    apd0.start_clock()
    apd1.start_clock()
    commune_clk.start()

    # Wait the end of communciation
    # We don't have to wait eve, because if alice and bob have finished, eve finished too
    Alice.communication_finished.wait()   # bloque jusqu'à la fin de la comm
    Bob.communication_finished.wait()


    keyAlice = sifting.sifting(Alice, Bob.chosen_bases) # For now, we don't simulate alice and bob basis communication (because is on public channel)
    keyBob = sifting.sifting(Bob, Alice.chosen_bases)

    if(len(keyAlice) != len(keyBob)):
        print(bcolors.FAIL + f"[ERROR] Alice and bob haven't same keys size !" + bcolors.ENDC)
    elif(keyAlice != keyBob):
        print(bcolors.WARNING + f"[WARN] Alice and bob haven't same keys ! ({how_much_key_corrupted(keyAlice, keyBob)}%)" + bcolors.ENDC)
    else:
        print(bcolors.OKGREEN + "[GOOD] Alice and bob have same keys !"+ bcolors.ENDC)

    (qber_value, final_key) = qber.qber_calculus(keyAlice, keyBob)

    if(qber_value < settings.qber_tolerance):
        print(bcolors.OKGREEN + f"[GOOD] Alice and Bob have a good qber value ({qber_value})%" + bcolors.ENDC)
    else:
        print(bcolors.FAIL + f"Qber is very high : {qber_value}. Communication aborting ..."+ bcolors.ENDC)
   

    if(eve_active):
        keyEve = sifting.eve_sifting(Eve, Alice.chosen_bases, Bob.chosen_bases)
        if(len(keyEve) != len(keyAlice)):
            print(bcolors.WARNING + f"Alice and Eve size's key aren't same :" + bcolors.ENDC)
        print(f"Eve got {how_much_key_corrupted(final_key, keyEve)} % of Alice key")
        

init_communication()

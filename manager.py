import clock
import sender
from quantum_canal import QuantumCanal # idk why i have to import only class and not file -_-
import receiver
import apd
import settings
import threading
import sifting
from utils.colors import bcolors
import qber

def init_communication():
    print("Initialisation en cours...")
    global Alice, Bob
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
    apd0.set_receiver(Bob)
    apd1.set_receiver(Bob)

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
    Alice.communication_finished.wait()   # bloque jusqu'à la fin de la comm
    Bob.communication_finished.wait()

    print("Echange terminé, place au sifting")

    keyAlice = sifting.sifting(Alice, Bob.receiver_basis) # For now, we don't simulate alice and bob basis communication (because is on public channel)
    keyBob = sifting.sifting(Bob, Alice.sending_basis)

    if(keyAlice != keyBob):
        print(bcolors.WARNING + "[ERROR] Alice and bob havn't same keys !")
        return False
    else:
        print(bcolors.OKGREEN + "[GOOD] Alice and bob have same keys !")

    print("Sifitng terminé, place au QBER")

    qber_value = qber.qber_calculus(keyAlice, keyBob)

    if(qber_value < settings.qber_tolerance):
        print(bcolors.OKGREEN + f"[GOOD] Alice and Bob have a good qber value ({qber_value})%")
    else:
        print(bcolors.WARNING + f"Qber is very high : {qber_value}. Communication aborting ...")

init_communication()

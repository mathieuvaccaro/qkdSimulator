import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # To import apd module :(

from components.apd import Apd


def test_without_delay():
    """Test manuel avec des apd parfaits (aucun dead time, gate toujours ouverte) : chaque photon envoyé doit être détecté
    """
    apd0 = Apd(0, clock_period=10, gate_off_duration=0,
               gate_on_duration=1000, dead_time=0)
    apd1 = Apd(1, clock_period=10, gate_off_duration=0,
               gate_on_duration=1000, dead_time=0)
    apd0.run()
    apd1.run()

    while True:
        print("El detector !")
        result = int(input("send photon ? (0/1)"))
        print("")
        if result == 0:
            apd0.receive_photon()
            print("Envoye (0)")
        elif result == 1:
            apd1.receive_photon()
            print("Envoye (1)")


def test_without_huge_deadtime():
    """Test manuel avec un dead time très élevé sur apd1 pour observer le blocage des détections successives
    """
    apd0 = Apd(0, 60, 0.01, 57, 8, 0.000098, 0.000002, 0.0005)
    #apd0 = Apd(0, clock_period=10, gate_off_duration=0, gate_on_duration=1000, dead_time=3000)
    apd1 = Apd(1, clock_period=10, gate_off_duration=0, gate_on_duration=1000, dead_time=3000)
    apd0.run()
    apd1.run()

    while True:
        print("El detector !")
        result = int(input("send photon ? (0/1)"))
        print("")
        if result == 0:
            apd0.receive_photon()
            print("Envoye (0)")
        elif result == 1:
            apd1.receive_photon()
            print("Envoye (1)")

def test_with_tiny_gateopen_duration():
    """Test manuel avec une fenêtre de détection (gate) nulle : aucune détection ne devrait aboutir
    """
    apd0 = Apd(0, clock_period=10, gate_off_duration=1000,
               gate_on_duration=0, dead_time=0)
    apd1 = Apd(1, clock_period=10, gate_off_duration=1000,
               gate_on_duration=0, dead_time=0)
    apd0.run()
    apd1.run()

    while True:
        print("El detector !")
        result = int(input("send photon ? (0/1)"))
        print("")
        if result == 0:
            apd0.receive_photon()
            print("Envoye (0)")
        elif result == 1:
            apd1.receive_photon()
            print("Envoye (1)")


if __name__ == "__main__":
    print("TESTING")
    print("1 - Test without any delay (perfects APD)")
    print("2 - Test with huge dead time")
    print("3 - Test with tiny gate open duration")
    result = int(input("What's your choice ?"))
    match result:
        case 1:
            test_without_delay()
        case 2:
            test_without_huge_deadtime()
        case 3:
            test_with_tiny_gateopen_duration()
        case _:
            print("Your choice isn't in the list. Aborting...")
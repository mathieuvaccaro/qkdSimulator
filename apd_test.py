import threading
from apd import Apd


# This test is with perfect APDs
def test_without_delay():
    apd0 = Apd(0, clock_period=10, gate_off_duration=0,
               gate_on_duration=1000, dead_time=0)
    apd1 = Apd(1, clock_period=10, gate_off_duration=0,
               gate_on_duration=1000, dead_time=0)
    apd0.run()
    apd1.run()

    thread_apd0 = threading.Thread(target=apd0.detect_photon)
    thread_apd0.start()
    thread_apd1 = threading.Thread(target=apd1.detect_photon)
    thread_apd1.start()

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
    apd0 = Apd(0, clock_period=10, gate_off_duration=0,
               gate_on_duration=1000, dead_time=3000)
    apd1 = Apd(1, clock_period=10, gate_off_duration=0,
               gate_on_duration=1000, dead_time=3000)
    apd0.run()
    apd1.run()

    thread_apd0 = threading.Thread(target=apd0.detect_photon)
    thread_apd0.start()
    thread_apd1 = threading.Thread(target=apd1.detect_photon)
    thread_apd1.start()

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
    apd0 = Apd(0, clock_period=10, gate_off_duration=1000,
               gate_on_duration=0, dead_time=0)
    apd1 = Apd(1, clock_period=10, gate_off_duration=1000,
               gate_on_duration=0, dead_time=0)
    apd0.run()
    apd1.run()

    thread_apd0 = threading.Thread(target=apd0.detect_photon)
    thread_apd0.start()
    thread_apd1 = threading.Thread(target=apd1.detect_photon)
    thread_apd1.start()

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
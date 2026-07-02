import qutip
from random import randint as rng
from random import sample as rng_s
import apd
from utils.colors import bcolors
import clock
import time
import settings
import numpy as np
import threading
import quantum_canal


class Receiver:
    # Rect states
    H = qutip.basis(2, 0)  # Horizontal
    V = qutip.basis(2, 1)  # Vertical
    # Diag states (45 et -45°)
    D = ((H + V) / np.sqrt(2)).unit()
    DM = ((H - V) / np.sqrt(2)).unit()
    STATES = {
        (0, 0): H,    # bit 0, rectiligne
        (1, 0): V,    # bit 1, rectiligne
        (0, 1): D,    # bit 0, diagonale
        (1, 1): DM,   # bit 1, diagonale
    }

    def __init__(self, apd0: apd.Apd, apd1: apd.Apd, quantum_channel, clk: clock.Clock):
        self.apd0 = apd0
        self.apd1 = apd1
        self.quantum_channel = quantum_channel
        self.clk = clk
        self.clk.subscribe(self.lost_qubits_detector)

        # État propre à chaque instance (plus au niveau de la classe)
        self.communication_en_cours = False

        # Une base et un bit par tick, gardés alignés index par index
        self.receiver_basis = []
        self.receiver_bits = []

        self.qubits_received = False
        self.message_size = settings.message_size  # Nombre de bits par QKD
        self.bit_number = -1  # index de bit, -1 car le sender démarre à 0
        self.communication_finished = threading.Event()

        # Protège les attributs partagés entre le thread d'horloge,
        # le détecteur de perte et le callback de l'APD
        self._lock = threading.Lock()

    # Si on démarre une nouvelle communication, on réinitialise tout
    def start_new_communication(self, clk: clock.Clock):
        with self._lock:
            self.receiver_basis = []
            self.receiver_bits = []
            self.qubits_received = False
            self.bit_number = -1
            self.communication_en_cours = False
            self.communication_finished.clear()
        # NB : on ne se ré-abonne PAS ici si on l'a déjà fait dans __init__,
        # sinon lost_qubits_detector serait appelé plusieurs fois par tick.
        # Ne garder l'abonnement qu'à un seul endroit.
        self.clk = clk

    # Appelée à chaque tick. On attend tolerance_message_not_receive ms ;
    # si "qubits_received" est toujours False, le qubit a été perdu.
    # On ajoute alors un marqueur -1 aux DEUX listes pour rester aligné.
    def lost_qubits_detector(self):
        time.sleep(settings.tolerance_message_not_receive / 1000)
        with self._lock:
            if self.qubits_received == False:
                self.receiver_bits.append(-1)
                self.receiver_basis.append(-1)  # garde l'alignement base <-> bit
                print(bcolors.WARNING + "BIT PERDU :)" + bcolors.ENDC)
                self.bit_number += 1
                if self.bit_number == self.message_size:
                    self.close_communication()
            self.qubits_received = False

    # Appelée juste après chaque tick. Une base est tirée au hasard et le
    # photon est mesuré dans cette base. Base ET bit sont enregistrés ensemble.
    def receive_qubits(self, sended_state):
        with self._lock:
            if self.bit_number == 0:
                print(bcolors.OKBLUE + "[RECEIVER] - START OF COMMUNICATION" + bcolors.ENDC)
                self.communication_en_cours = True

            basis = rng(0, 1)
            receiver_basis_x = self.STATES[(0, basis)]
            receiver_basis_y = self.STATES[(1, basis)]

            # Mesure du qubit dans la base choisie
            measure = qutip.measurement.measure(
                sended_state,
                [qutip.ket2dm(receiver_basis_x), qutip.ket2dm(receiver_basis_y)]
            )[0]

            # On enregistre base + bit de façon atomique, dans le même bloc.
            # L'appel aux APD reste pour la fidélité de la simulation, mais
            # le bit qui alimente la clé provient directement de la mesure,
            # ce qui supprime la course avec le callback asynchrone add_bits.
            self.receiver_basis.append(basis)
            self.receiver_bits.append(measure)
            self.read_bits(measure)

            self.qubits_received = True
            self.bit_number += 1

            if self.bit_number == self.message_size:
                self.close_communication()

    def close_communication(self):
        print(bcolors.OKBLUE + "[RECEIVER] - END OF COMMUNICATION" + bcolors.ENDC)
        self.communication_en_cours = False
        self.communication_finished.set()  # débloque ceux qui attendent
        self.clk.stop()

    # Déclenche l'APD correspondante (side effect de simulation).
    def read_bits(self, measure):
        if measure == 0:
            self.apd0.receive_photon()
        elif measure == 1:
            self.apd1.receive_photon()

    # Conservée pour compatibilité si l'APD veut notifier le receiver.
    # NE PLUS appender ici : le bit est déjà enregistré dans receive_qubits,
    # sinon on aurait un doublon et un nouveau décalage.
    def add_bits(self, bit):
        pass

    def get_last_sifting_info(self):
        return (self.receiver_basis, self.receiver_bits)
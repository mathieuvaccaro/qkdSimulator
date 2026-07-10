from random import randint as rng
import components.quantum_canal as quantum_canal
from utils.colors import bcolors
import components.clock as clock
import settings
import numpy as np
import qutip
import threading
import protocols.protocol_manager as pm
import utils.progress_bar as pb

class Sender:
    message_size = settings.message_size

    def __init__(self, quantum_channel : quantum_canal.QuantumCanal, clk: clock.Clock):
        """Initialise l'émetteur (Alice) avec le canal quantique et la clock commune

        Args:
            quantum_channel (quantum_canal.QuantumCanal): canal quantique d'émission
            clk (clock.Clock): clock commune de synchronisation
        """
        self.quantum_channel = quantum_channel
        self.sent_qubit_count = 0
        self.chosen_bases = []
        self.sent_bits = []
        self.clk = clk
        self.communication_finished = threading.Event()
        self.STATES = pm.get_states()

    def emit_qubit(self):
        """La fonction emit_qubit se lance de manière synchrone avec la clock commune (défini dans manager.py)
        A chaque tick un qubit est encodé de manière aléatoire (bit et base random) et est ensuite transmis sur le canal quantique (quantum_canal.py)"""
        
        # On s'arrête dès que tout le message a été émis (exactement message_size qubits).
        if(self.sent_qubit_count == self.message_size):
            return

        bit = rng(0, 1)
        chosen_basis = rng(0, 1)
        self.sent_bits.append(bit)
        self.chosen_bases.append(chosen_basis)
        qubit = self.STATES[(bit, chosen_basis)]

        # Le nombre de photon émis par le sender suit une loi de poisson (voir settings.py)
        # si le settings.average_emitted_photon == -1, alors on émet tout le temps un et un seul photon
        number_photon_emitted = 1 if settings.average_emitted_photon == -1 else np.random.poisson(settings.average_emitted_photon)
        for _ in range(number_photon_emitted):
            self.send_qubit(qubit)

        self.sent_qubit_count += 1

        pb.progress_bar(self.sent_qubit_count, self.message_size)

        if(self.sent_qubit_count >= self.message_size):
            # Débloque le manager.py permettant de passer a la suite
            self.communication_finished.set()

    def send_qubit(self, qubit : qutip.qobj):
        """Émet le qubit sur le canal quantique

        Args:
            qubit (qutip.qobj): qubit à émettre
        """
        self.quantum_channel.send_qubit(qubit)
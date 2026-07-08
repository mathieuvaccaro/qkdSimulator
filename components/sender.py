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


# Emitting exactly one photon is very difficult; one method is to use an
# attenuated laser. In this simulation we approximate that with an average
# number of emitted photons (perfectly 1 here).
class Sender:
    message_size = settings.message_size

    def __init__(self, quantum_channel : quantum_canal.QuantumCanal, clk: clock.Clock):
        self.quantum_channel = quantum_channel
        self.sent_qubit_count = 0
        self.chosen_bases = []
        self.sent_bits = []
        self.clk = clk
        self.communication_finished = threading.Event()  # lets main know when it's finished
        self.STATES = pm.get_states()

    def emit_qubit(self):
        # On s'arrête dès que tout le message a été émis (exactement message_size qubits).
        if(self.sent_qubit_count >= self.message_size):
            return

        bit = rng(0, 1)
        chosen_basis = rng(0, 1)
        self.sent_bits.append(bit)
        self.chosen_bases.append(chosen_basis)
        qubit = self.STATES[(bit, chosen_basis)]

        # How much photon will be sended
        if(settings.average_emitted_photon == -1):
            number_photon_emitted = 1
        else:
            number_photon_emitted = np.random.poisson(settings.average_emitted_photon)
        # Emit n photons
        for _ in range(number_photon_emitted):
            self.send_qubit(qubit)

        self.sent_qubit_count += 1
        pb.progress_bar(self.sent_qubit_count, self.message_size)

        if(self.sent_qubit_count >= self.message_size):
            self.communication_finished.set()   # unblock anyone waiting

    def send_qubit(self, qubit : qutip.qobj):
        self.quantum_channel.send_qubit(qubit)
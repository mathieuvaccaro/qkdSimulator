from random import randint as rng
import quantum_canal
from utils.colors import bcolors
import clock
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
    communication_in_progress = False
    message_size = settings.message_size

    def __init__(self, quantum_channel, clk: clock.Clock):
        self.quantum_channel = quantum_channel
        self.sent_qubit_count = 0
        self.chosen_bases = []
        self.sent_bits = []
        self.clk = clk
        self.clk.subscribe(self.emit_qubit)
        self.communication_finished = threading.Event()  # lets main know when it's finished
        self.STATES = pm.get_states()

    def emit_qubit(self):
        if self.sent_qubit_count == 0:
            print(bcolors.OKBLUE + "[SENDER] - Start communication" + bcolors.ENDC)
            self.communication_in_progress = True

        bit = rng(0, 1)
        chosen_basis = rng(0, 1)
        self.sent_bits.append(bit)
        self.chosen_bases.append(chosen_basis)
        qubit = self.STATES[(bit, chosen_basis)]


        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        pb.progress_bar(self.sent_qubit_count, self.message_size)

        if self.sent_qubit_count == self.message_size:
            print(bcolors.OKBLUE + "[SENDER] END OF COMMUNICATION" + bcolors.ENDC)
            self.communication_in_progress = False
            self.communication_finished.set()   # unblock anyone waiting

    def send_qubit(self, qubit):
        self.quantum_channel.send_qubit(qubit)
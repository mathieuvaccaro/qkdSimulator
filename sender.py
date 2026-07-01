from random import randint as rng
import quantum_canal
from utils.colors import bcolors
import clock
import settings
import numpy as np
import qutip

# It's very difficult to emit only one photon, one of method is to use attenuate laser.
# In this simulation, we will simulate that by a average factor of emitted photon (perfectly 1)
class Sender:
    message_size = settings.message_size

    H = qutip.basis(2, 0)
    V = qutip.basis(2, 1)
    D = ((H + V) / np.sqrt(2)).unit()
    DM = ((H - V) / np.sqrt(2)).unit()

    STATES = {
        (0, 0): H,   # bit 0, rectiligne
        (1, 0): V,   # bit 1, rectiligne
        (0, 1): D,   # bit 0, diagonale
        (1, 1): DM,  # bit 1, diagonale
    }

    def __init__(self, quantum_channel, clk : clock.Clock):
        self.quantum_channel = quantum_channel
        self.bit_number = 0
        self.sending_basis = []
        self.sending_bits = []
        self.clk = clk
        self.clk.subscribe(self.creating_qubit)

    def start_new_communication(self):
        self.sending_basis = []
        self.sending_bits = []

    def creating_qubit(self):
        if self.bit_number == 0:
            print(bcolors.OKBLUE + "[SENDER] - Start communication" + bcolors.ENDC)
        
        bit = rng(0, 1)
        basis = rng(0, 1)
        self.sending_bits.append(bit)
        self.sending_basis.append(basis)

        qubit = self.STATES[(bit, basis)]
        print("-----------------------------")
        print(f"Bit n°{self.bit_number} ({bit}) envoyé")
        self.send_qubit(qubit)

        self.bit_number += 1
        if self.bit_number == self.message_size:
            #self.bit_number = 0 # Just in case
            #self.start_new_communication() # Just in case
            print(bcolors.OKBLUE + "[SENDER] END OF COMMUNICATION" + bcolors.ENDC)



    def send_qubit(self, qubit):
        self.quantum_channel.send_qubit(qubit)

    def get_last_sifting_info(self):
        return (self.sending_basis, self.sending_bits)
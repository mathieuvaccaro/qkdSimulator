import qutip
from random import randint as rng
from random import sample as rng_s
import apd
from utils.colors import bcolors
import clock
import time
import settings
import numpy as np
import quantum_canal
class Receiver:


    # Rect states
    H = qutip.basis(2, 0) # Horizontal
    V = qutip.basis(2, 1) # Vertical

    # Diag sates (45 et -45°)
    D = ((H+V) / np.sqrt(2)).unit() 
    DM = ((H-V) / np.sqrt(2)).unit()
    STATES = {
        (0, 0): H,    # bit 0, rectiligne
        (1, 0): V,    # bit 1, rectiligne
        (0, 1): D,    # bit 0, diagonale
        (1, 1): DM,   # bit 1, diagonale
    }

    def __init__(self, apd0 : apd.Apd, apd1 : apd.Apd, quantum_channel, clk : clock.Clock):
        self.apd0 = apd0
        self.apd1 = apd1
        self.quantum_channel = quantum_channel
        self.clk = clk
        self.clk.subscribe(self.lost_qubits_detector)

        # A basis created for each communication to contains used basis
        self.receiver_basis = []
        self.receiver_bits = []
        self.qubits_received = False # Turn to true
        self.message_size = settings.message_size # Number of bits for each QKD
        self.bit_number = -1 # index of bit, -1 beacause, sender start with 0


    # If we start a new communication, we have to reset all stocked values
    def start_new_communication(self, clk: clock.Clock):
        self.receiver_basis = []
        self.receiver_bits = []
        self.clk = clk
        self.clk.subscribe(self.lost_qubits_detector)


    # Each tic this function is called, we wait tolerance_message_not_receive ms, if "qubits_received" is false, the qubits wasn't recieve, however it was``
    # If bit wasn't received, we attribute -1 value to receiver_bits
    def lost_qubits_detector(self):
        time.sleep(settings.tolerance_message_not_receive/1000)
        if(self.qubits_received == False):   
            self.receiver_bits.append(-1)
            print(bcolors.WARNING + "BIT PERDU :)" + bcolors.ENDC)
            self.bit_number+=1
            if(self.bit_number == self.message_size):
                self.close_communication()
        self.qubits_received = False
        


    # NOTE : Passer par un objet ?

    # Usually, this fonction is called right after each tick
    # A base is randomly selected and photon is measured in this specific basis
    def receive_qubits(self, sended_state):
        if(self.bit_number == 0):
            print(bcolors.OKBLUE + "[RECEIVER] - START OF COMMUNICATION" + bcolors.ENDC)

        basis = rng(0, 1)
        self.receiver_basis.append(basis)
        receiver_basis_x = self.STATES[(0, basis)]
        receiver_basis_y = self.STATES[(1, basis)]
        self.bit_number += 1
        print(f"Reception : {self.bit_number}")

        # Warning : here measure is good bits, but for the simulation we will read associate bits with APDs (however no side channels attack is possible)
        measure = qutip.measurement.measure(sended_state, [qutip.ket2dm(receiver_basis_x), qutip.ket2dm(receiver_basis_y)])[0]
        self.read_bits(measure)

        self.qubits_received = True

        if(self.bit_number == self.message_size):
            self.close_communication()           
             #self.bit_number = 0
            #self.start_new_communication()

    def close_communication(self):
        print(bcolors.OKBLUE + "[RECEIVER] - END OF COMMUNICATION" + bcolors.ENDC)
        self.clk.stop()

    # This function called apd
    def read_bits(self, measure):
        if(measure == 0):
            self.apd0.receive_photon()
        elif(measure == 1):
            self.apd1.receive_photon()

    # This function is called by apd
    def add_bits(self, bit):
        self.receiver_bits.append(bit)

    def get_last_sifting_info(self):
        return (self.receiver_basis, self.receiver_bits)
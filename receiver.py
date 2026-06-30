import qutip
from random import randint as rng
from random import sample as rng_s
import apd
from utils.colors import bcolors

# A basis created for each communication to contains used basis
receiver_basis = []
receiver_bits = []
apd0 = apd.Apd(0, 60, 0.01, 4, 8.5, 0.000098, 0.000002, 0.0005)
apd1 = apd.Apd(1, 60, 0.01, 4, 8.5, 0.000098, 0.000002, 0.0005)
message_size = 1000 # Number of bits for each QKD
bit_number = 0 # index of bit

STATES = {
    (0, 0): H,    # bit 0, rectiligne
    (1, 0): V,    # bit 1, rectiligne
    (0, 1): D,    # bit 0, diagonale
    (1, 1): DM,   # bit 1, diagonale
}

# If we start a new communication, we have to reset all stocked values
def start_new_communication():
    global receiver_basis 
    global receiver_bits 
    receiver_basis = []
    receiver_bits = []

# A base is randomly selected and photon is measured in this specific basis
def receive_qubits(sended_state):
    if(bit_number == 0):
        print(bcolors.OKBLUE + "START OF COMMUNICATION")

    basis = rng(0, 1)
    receiver_basis.append(basis)
    receiver_basis_x = STATES[0, receiver_basis]
    receiver_basis_y = STATES[1, receiver_basis]
    bit_number += 1

    # Warning : here measure is good bits, but for the simulation we will read associate bits with APDs (however no side channels attack is possible)
    measure = qutip.measurement.measure(sended_state, [qutip.ket2dm(receiver_basis_x), qutip.ket2dm(receiver_basis_y)])[0]
    read_bits(measure)

    if(bit_number == message_size):
        bit_number = 0
        start_new_communication()
        print(bcolors.OKBLUE + "END OF COMMUNICATION")

# This function called apd
def read_bits(measure):
    if(measure == 0):
        apd0.receive_photon()
    elif(measure == 1):
        apd1.receive_photon()

# This function is called by apd
def add_bits(bit):
    receiver_bits.append(bit)

def get_last_sifting_info():
    return (receiver_basis, receiver_bits)
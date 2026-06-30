import random
import receiver

noise = 20 # in %

def send_qubits(qubits):
    if(random.randint(0, 100) >= noise):
        receiver.receive_qubits(qubits)
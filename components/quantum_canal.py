import random
import qutip
import settings
from utils.colors import bcolors

class QuantumCanal:
    interceptor = None  # set only when an attack is active (see manager)

    def setReceiver(self, receiver):
        self.receiver = receiver
    
    def setSender(self, sender):
        self.sender = sender

    def setInterceptor(self, interceptor):
        self.interceptor = interceptor

    def send_qubit(self, qubit, from_eve = False):
        # If an attack is active, qubits from Alice go to Eve first (interceptor),
        # then Eve's re-emitted qubits (from_eve) go to Bob.
        cible = self.interceptor if (self.interceptor is not None and not(from_eve)) else self.receiver
        random_value = random.randint(0, 100)
        if(random_value < settings.quantum_canal_bit_loss):
            pass
        elif(random_value < settings.quantum_canal_bit_flip + settings.quantum_canal_bit_loss):
            cible.receive_qubit(qutip.sigmay() * qubit)
        else:
            cible.receive_qubit(qubit)
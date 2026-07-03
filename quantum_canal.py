import random
import qutip
import settings
from utils.colors import bcolors

class QuantumCanal:
    def setReceiver(self, receiver):
        self.receiver = receiver
    
    def setSender(self, sender):
        self.sender = sender

    def setInterceptor(self, interceptor):
        self.interceptor = interceptor

    def send_qubit(self, qubit, from_eve = False):
        # Eve is present, so receiver is maybe eve (or bob)
        cible = self.interceptor if (settings.eve_present and not(from_eve)) else self.receiver
        random_value = random.randint(0, 100)
        if(random_value < settings.quantum_canal_bit_loss):
            pass
        elif(random_value < settings.quantum_canal_bit_flip + settings.quantum_canal_bit_loss):
            cible.receive_qubit(qutip.sigmay() * qubit)
        else:
            cible.receive_qubit(qubit)
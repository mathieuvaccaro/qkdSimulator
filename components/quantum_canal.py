import random
import qutip
import settings
from utils.colors import bcolors

"""Le canal fonctionne de manière de relais en fonction de qui envoie le qubit (Alice ou Eve)
 -> cas n°1 : Alice envoie le qubit et eve n'est pas présente -> le qubit va direction bob (receiver)
 -> cas n°2 : Alice envoie le qubit et eve est présente -> le qubit va direction eve (interceptor)
 -> cas n°3 : Eve envoie le qubit -> le qubit va direction bob"""

class QuantumCanal:
    interceptor = None 

    def setReceiver(self, receiver):
        self.receiver = receiver
    
    def setSender(self, sender):
        self.sender = sender

    def setInterceptor(self, interceptor):
        self.interceptor = interceptor

    def send_qubit(self, qubit, from_eve = False):
        # En fonction du cas, la cible diffère
        cible = self.interceptor if (self.interceptor is not None and not(from_eve)) else self.receiver
        
        random_value = random.randint(0, 100)
        # Les qubits qui n'arriveront jamais a destination (Rest In Peace)
        if(random_value < settings.quantum_canal_bit_loss):
            pass
        
        # Les qubits qui ont switch (0 <-> 1), pour cela on applique une porte sigmay
        elif(random_value < settings.quantum_canal_bit_flip + settings.quantum_canal_bit_loss):
            cible.receive_qubit(qutip.sigmay() * qubit)

        # Les qubits qui sont passés (les warriors) 
        else:
            cible.receive_qubit(qubit)
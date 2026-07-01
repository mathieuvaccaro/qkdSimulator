import random
import receiver
import settings

# Quantum channel isn't a perfect channel

noise = settings.quantum_canal_noise # in %

class QuantumCanal:
    def setReceiver(self, receiver):
        self.receiver = receiver
    
    def setSender(self, sender):
        self.sender = sender

    def send_qubit(self, qubit):
        if(random.randint(0, 100) >= noise):
            self.receiver.receive_qubits(qubit)
        else:
            print("Le qubit s'est perdu dans le canal :(")
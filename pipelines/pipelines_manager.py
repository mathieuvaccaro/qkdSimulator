import components.quantum_canal
import random
import qutip
import settings
from utils.colors import bcolors

class PipelineManager():

    def __init__(self, sender, receiver, interceptor, clk):
        self.active_attacks = []
        self.interceptor = None  # set only when an attack is active
        
        # Pipeline 1 : source emit

        # Pipelien 2 : canal
        self.quantum_canal = components.quantum_canal.QuantumCanal()



    def setReceiver(self, receiver):
        self.receiver = receiver
    
    def setSender(self, sender):
        self.sender = sender

    def setInterceptor(self, interceptor):
        self.interceptor = interceptor

    # Enable an attack
    def subscribe(self, attack):
        self.active_attacks.append(attack)

# ----------------------------

    def source_emit_pipeline():
        pass

    def quantum_channel_pipeline(self, source, qubit, from_eve = False):
        cible = self.interceptor if (self.interceptor is not None and not(from_eve)) else self.receiver
        random_value = random.randint(0, 100)

        # From Alice
        if(not(from_eve)):
            for i in self.active_attacks:
                if i.type == "quantum_channel":
                    i.attack_function()
                    return # J'ai un doute sur le return ici
            
        # From eve    
        if(random_value < settings.quantum_canal_bit_loss):
            pass
        elif(random_value < settings.quantum_canal_bit_flip + settings.quantum_canal_bit_loss):
            cible.receive_qubit(qutip.sigmay() * qubit)
        else:
            cible.receive_qubit(qubit)
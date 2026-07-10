import qutip
from random import randint as rng
from utils.colors import bcolors
from intercept.factory import Intercept
from components.apd import Apd
from components.quantum_canal import QuantumCanal
from components.clock import Clock
from components.sender import Sender
from components.receiver import Receiver

class InterceptAndResent(Intercept):
    """L'attaque intercept and resent et simplement "l'attaque par défaut". Eve arrive à se situer entre Alice et Bob sur le canla de communication
    Elle va se contenter de mesurer les qubits émis par Alice dans une base aléatoire, le ré-encoder et le transmettre à Bob.

    QBER Estimé : 25%
    Conaissance de clé : 50%
    Détectable : Oui
    Args:
        Intercept (_type_): Héritage de intercept (factory.py)
    """
    
    def __init__(self, apdEve0 : Apd, apdEve1 : Apd , quantum_canal : QuantumCanal, commune_clk : Clock, alice : Sender, bob : Receiver):
        print(bcolors.OKCYAN + "[CLASSIC ATTACK INTERCEPT AND RESENT] ..." + bcolors.ENDC)
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)


    def receive_qubit(self, qubit : qutip.Qobj):
        """Cette fonction est appelé par le canal quantique lorsuqe un qubit est arrivé

        Args:
            qubit (qutip.qobj): qubit recu par le canal.
        """          
        with self._lock:
            if(self.qubit_received == True):
                self.already_receive_photon()
            else:
                chosen_basis = rng(0, 1)
                self.chosen_bases.append(chosen_basis)

                measured_bit = self.trigger_apd(qubit)

                resent_qubit = self.STATES[(measured_bit, chosen_basis)]
                self.emit_qubit(resent_qubit)

                self.qubit_received = True

    # Réémet vers Bob l'état reconstruit par Eve (from_eve=True côté canal).
    def emit_qubit(self, qubit : qutip.Qobj):
        """La fonction emit_qubit se lance de manière synchrone avec la clock commune (défini dans manager.py)
        A chaque tick un qubit est encodé de manière aléatoire (bit et base random) et est ensuite transmis sur le canal quantique (quantum_canal.py)

        Args:
            qubit (qutip.Qobj): qubit à émettre sur le canal
        """        
        self.send_qubit(qubit)
        self.sent_qubit_count += 1
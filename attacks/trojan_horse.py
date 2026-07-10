"""L'attaque trojan horse repose sur le fait d'emttre un faisceau lumineux vers le récepteur """

from utils.colors import bcolors
from intercept.factory import Intercept
from components.receiver import Receiver 
import qutip
from random import randint as rng
from components.sender import Sender
from components.receiver import Receiver
from components.apd import Apd
from components.quantum_canal import QuantumCanal
from components.clock import Clock

class TrojanHorse(Intercept):
    """L'attaque trojan horse repose sur le faite que Eve peut envoyer un faisceau lumineux intense sur l'émetteur d'Alice (contenant la base d'encodage). 
    De par la loi de Fresnel, une partie de la lumière est réfléchi en contenant l'information de la base utilisant pour la lecture

    Remarque : Il est difficile (même impossible) d'envoyer un faisceau lumineux dans un émetteur en simulant un programme Python. il s'agit donc 
    d'une simulation brève en supposant qu'on y arrive.

    QBER Estimé : 0%
    Clé Estimé : 100%
    Détectable : Non

    Args:
        Intercept (_type_): Héritage de factory.py dans intercept
    """    
        
    def __init__(self, apdEve0 : Apd, apdEve1 : Apd, quantum_canal : QuantumCanal, commune_clk : Clock, alice : Sender, bob : Receiver):
        print(bcolors.OKCYAN + "[ATTACK TROJAN HORSE] ..." + bcolors.ENDC)
        self.alice = alice
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)

    def get_cible_basis(self) -> int:
        """Récupère la base à cibler : celle utilisée par Alice au dernier tick (supposée connue via le faisceau espion), ou une base aléatoire si aucune n'est encore disponible

        Returns:
            int: base à utiliser (0 ou 1)
        """
        if(len(self.chosen_bases) == 0):
            return rng(0,1)
        return self.alice.chosen_bases[-1]
    
    def receive_qubit(self, sent_state : qutip.Qobj):
        """Cette fonction est appelé par le canal quantique lorsuqe un qubit est arrivé

        Args:
            sent_state (qutip.Qobj): qubit recu par le canal.
        """        
        with self._lock:
            if(self.qubit_received == True):
                self.already_receive_photon()
            else:
                # Eve a (supposement) récupérer la base de bob grâce a une impulsion lumineuse
                chosen_basis = self.get_cible_basis()
                self.chosen_bases.append(chosen_basis)

                measured_bit = self.trigger_apd(sent_state)

                # Comme la base est celle de Bob, réémettre l'état mesuré n'introduit aucune erreur : l'attaque reste indétectable.
                resent_qubit = self.STATES[(measured_bit, chosen_basis)]
                self.send_qubit(resent_qubit)

                self.qubit_received = True
                self.received_qubit_count += 1

    def emit_qubit(self, bit : int):
        """La fonction emit_qubit se lance de manière synchrone avec la clock commune (défini dans manager.py)
        A chaque tick un qubit est encodé de manière aléatoire (bit et base random) et est ensuite transmis sur le canal quantique (quantum_canal.py)

        Args:
            bit (int): bit à encoder puis émettre
        """
        if self.sent_qubit_count == 0:
            self.communication_in_progress = True
        qubit = self.STATES[(bit, self.get_cible_basis())]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        if self.sent_qubit_count == self.message_size:
            self.communication_in_progress = False

import qutip
from utils.colors import bcolors
from intercept.factory import Intercept
import settings
from random import randint as rng
from components.apd import Apd
from components.quantum_canal import QuantumCanal
from components.clock import Clock
from components.sender import Sender
from components.receiver import Receiver


class DoubleClickEvent(Intercept):
    """L'attaque par exploitation du double click event repose sur un principe simple.
    Dans l'éventualité ou Bob recoit plusieurs photons il a plusieurs possibilités
    - Dans le doute jeter les photons et noté la réception comme perdu
    - Choisir aléatoirement un photon
    Dans l'attaque c'est ce premier cas qui va nous intéresser. Lors de l'intercept and resent, Eve va renvoyer un grand nombre de photons. Si la base choisit
    par eve est la même que celle de bob, le photon sera correctement lu par un seul APD -> Pas de problème
    Dans le cas ou la bse n'est pas la même (et donc normalemnet une augmentation du QBER), les différents photons vont actionner les deux APDs de réception,
    ainsi si Bob décide de jeter les photons, le qubit sera considérer comme perdu, et le qber n'augmentera pas.

    QBER Estimé : 0%
    Clé Estimé : 100%
    Détectable : Non

    Args:
        Intercept (_type_): Héritage de factory.py dans intercept
    """    

    def __init__(self, apdEve0 : Apd, apdEve1 : Apd , quantum_canal : QuantumCanal, commune_clk : Clock, alice : Sender, bob : Receiver):
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)


    def receive_qubit(self, qubit : qutip.Qobj):
        """Cette fonction est appelé par le canal quantique lorsuqe un qubit est arrivé

        Args:
            qubit (qutip.qobj): qubit recu par le canal.
        """          
        with self._lock:
            if(self.received_qubit_count <= self.message_size):
                if(self.qubit_received == True):
                    self.already_receive_photon()
                else:
                    chosen_basis = rng(0, 1)
                    self.chosen_bases.append(chosen_basis)

                    measured_bit = self.trigger_apd(qubit)

                    resent_qubit = self.STATES[(measured_bit, chosen_basis)]
                    self.emit_qubit(resent_qubit)

                    self.qubit_received = True

            else:
                self.finished = True

    # Réémet vers Bob l'état reconstruit par Eve (from_eve=True côté canal).
    def emit_qubit(self, qubit : qutip.Qobj):
        """La fonction emit_qubit se lance de manière synchrone avec la clock commune (défini dans manager.py)
        A chaque tick un qubit est encodé de manière aléatoire (bit et base random) et est ensuite transmis sur le canal quantique (quantum_canal.py)

        Args:
            qubit (qutip.Qobj): qubit à émettre sur le canal
        """
        for i in range(settings.emission_click_event):
            self.send_qubit(qubit)
        self.sent_qubit_count += 1
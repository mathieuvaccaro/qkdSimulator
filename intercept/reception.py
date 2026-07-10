import time
import qutip
from random import randint as rng

import settings
from utils.colors import bcolors

# Reception side of the interceptor: it reads (measures) the qubits emitted by
# the sender. Attributes used here (STATES, lock, counters, apds...) are created
# by the factory (see intercept.factory).
class ReceptionMixin:

    def detect_lost_qubit(self):
        """Détecte les qubits perdus : après tolerance_message_not_receive ms sans réception, marque le slot par un -1 dans les deux listes pour garder l'alignement base <-> bit
        """
        time.sleep(settings.tolerance_message_not_receive / 1000)
        if(self.finished == False):
            with self._lock:
                if self.qubit_received == False:
                    self.measured_bits.append(-1)
                    self.chosen_bases.append(-1)  # keep basis <-> bit alignment
                    self.received_qubit_count += 1
                self.qubit_received = False

    def already_receive_photon(self):
        """Appelée lorsque plus d'un photon est reçu pour une même détection ; ici on se contente d'en compter l'occurrence
        """
        self.nb+=1
        pass

    def prepare_bases(self, init = False):
        """Prépare (tire au sort) la base de lecture en amont de la réception du qubit

        Args:
            init (bool, optional): drapeau d'activation piloté par la clock. Defaults to False.
        """
        # Cette fonction tourne grace a la clock mais est activé grace a "init"
        
        if(self.received_qubit_count < self.message_size):
            chosen_basis = rng(0, 1)
            basis_state_0 = self.STATES[(0, chosen_basis)]
            basis_state_1 = self.STATES[(1, chosen_basis)]
            self.chosen_bases.append(int(chosen_basis))

    def receive_qubit(self, sent_state : qutip.Qobj):
         """Appelée par le canal quantique à l'arrivée d'un qubit : une base est tirée au sort et le qubit est mesuré dans cette base (base ET bit enregistrés ensemble)

         Args:
             sent_state (qutip.Qobj): qubit reçu par le canal
         """
         with self._lock:
            if(self.received_qubit_count <= self.message_size):
                if(self.qubit_received == True):
                    self.already_receive_photon()
                else:
                    # Measure the qubit in the chosen basis
                    if(len(self.chosen_bases) == 0):
                        return
                    
                  
                    self.trigger_apd(sent_state)

                    self.qubit_received = True
                    self.received_qubit_count += 1

            else:
                self.finished = True

    def trigger_apd(self, qubit : qutip.qobj):
        """Mesure le qubit dans la base courante, déclenche l'apd correspondant (effet de bord de simulation) et renvoie le bit mesuré

        Args:
            qubit (qutip.qobj): qubit à mesurer

        Returns:
            int: bit mesuré (0 ou 1)
        """
        basis_state_0 = self.STATES[(0, self.chosen_bases[-1])]
        basis_state_1 = self.STATES[(1, self.chosen_bases[-1])]
        measured_bit = qutip.measurement.measure(qubit,[qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)])[0]

        if measured_bit == 0:
            self.apd0.receive_photon()
        elif measured_bit == 1:
            self.apd1.receive_photon()

        return measured_bit

    def read_value(self, value : int):
        """Appelée par l'apd : enregistre le bit lu dans la liste des bits mesurés

        Args:
            value (int): bit lu par l'apd
        """
        self.measured_bits.append(value)
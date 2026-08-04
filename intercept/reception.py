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
                    self.pending_index += 1
                    self.slot += 1
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
        
        if(self.slot < self.message_size):
            chosen_basis = rng(0, 1)
            basis_state_0 = self.STATES[(0, chosen_basis)]
            basis_state_1 = self.STATES[(1, chosen_basis)]
            self.set_current_basis(chosen_basis) 

    def set_current_basis(self, chosen_basis : int):
        """ Avance d'un slot et y enregistre la base de lecture choisie.

        Les listes étant pré-allouées, on écrit à l'index courant au lieu de faire un append :
        base et bit restent ainsi alignés même quand l'apd d'Eve ne déclenche pas (gate fermée
        ou dead time en cours), cas où read_value n'est jamais appelée et où le -1 reste en place.

        Args:
            chosen_basis (int): base de lecture du slot courant (0 ou 1)
        """
        self.pending_index += 1
        if(0 <= self.pending_index < len(self.chosen_bases)):
            self.chosen_bases[self.pending_index] = int(chosen_basis)

    def receive_qubit(self, sent_state : qutip.Qobj):
         """Appelée par le canal quantique à l'arrivée d'un qubit : une base est tirée au sort et le qubit est mesuré dans cette base (base ET bit enregistrés ensemble)

         Args:
             sent_state (qutip.Qobj): qubit reçu par le canal
         """
         with self._lock:
            if(self.slot <= self.message_size):
                if(self.qubit_received == True):
                    self.already_receive_photon()
                else:
                    # Measure the qubit in the chosen basis
                    if(self.pending_index < 0):
                        return
                    
                  
                    self.trigger_apd(sent_state)

                    self.qubit_received = True
                    self.slot += 1

            else:
                self.finished = True

    def trigger_apd(self, qubit : qutip.qobj):
        """Mesure le qubit dans la base courante, déclenche l'apd correspondant (effet de bord de simulation) et renvoie le bit mesuré

        Args:
            qubit (qutip.qobj): qubit à mesurer

        Returns:
            int: bit mesuré (0 ou 1)
        """
        basis_state_0 = self.STATES[(0, self.chosen_bases[self.pending_index])]  # * base du slot courant (avant : dernier append)
        basis_state_1 = self.STATES[(1, self.chosen_bases[self.pending_index])]  # *
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
        if(0 <= self.pending_index < len(self.measured_bits)):
            self.measured_bits[self.pending_index] = value 



    def eve_sifting(self, alice_bases : list[int], bob_bases : list[int]) -> list[int]:
        """Sifting du point de vue d'Eve : elle ne garde que les bits mesurés là où Alice et Bob ont utilisé la même base.
        Si Eve avait choisi une autre base qu'Alice et Bob, le bit conservé sera erroné (mauvaise base de lecture).

        Petite particularité : dans le cas de l'attaque par time correlations, le sifting ne se fait pas aproprement parler.

        Args:
            eve: intercepteur (Eve) contenant ses bases et bits mesurés
            alice_bases (list[int]): bases d'Alice révélées publiquement
            bob_bases (list[int]): bases de Bob révélées publiquement

        Returns:
            list[int]: clé reconstruite par Eve
        """
        key = []
        for i in range(len(self.chosen_bases)):
            if(alice_bases[i] == bob_bases[i]):
                key.append(self.measured_bits[i])
        return key
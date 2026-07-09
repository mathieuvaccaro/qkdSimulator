"""L'attaque PNS repose sur le principe suivant :
L'emetteur émet plus d'un photon en moyenne,
Lorsque un seul photon est émis, eve le détruit,
Lorsque que plus d'un photon est émis, eve en mesure un et le garde pour lui et laisse passer le deuxième telle quelle
"""
import qutip
from utils.colors import bcolors
from intercept.factory import Intercept

import qutip
from random import randint as rng

class Pns(Intercept):
    
    def __init__(self, apdEve0, apdEve1, quantum_canal, commune_clk, Alice, Bob):
        print(bcolors.OKCYAN + "[ATTACK PNS] ..." + bcolors.ENDC)
        self.second_photon = 0 # We want to intercept only one photon, so we have to add a variable
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk)

    def receive_qubit(self, sent_state : qutip.Qobj):
        with self._lock:
            if(self.qubit_received == True): # Il ne voit pas self.qubit_received a true ....
                if(self.second_photon == 1): 
                    self.already_receive_photon(sent_state)
                self.second_photon = 2
            else:
                self.send_qubit(sent_state)
                self.second_photon = 1
                self.qubit_received = True

                self.chosen_bases.append(-1) # We add temp value, wich are modified if we are able to measure a photon
                self.measured_bits.append(-1)

    def emit_qubit(self, bit : int):
        if self.sent_qubit_count == 0:
            self.communication_in_progress = True
        qubit = self.STATES[(bit, self.chosen_bases[len(self.chosen_bases)-1])]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        if self.sent_qubit_count == self.message_size:
            self.communication_in_progress = False
            self.communication_finished.set()   # unblock anyone waiting

    def already_receive_photon(self, sent_state):
        # Eve garde ce photon (le 2e) et le mesure. On fixe d'abord la base
        # (chosen_bases[-1], jusqu'ici à -1) car trigger_apd la lit pour mesurer.
        chosen_basis = rng(0, 1)
        self.chosen_bases[-1] = chosen_basis

        measured_bit = self.trigger_apd(sent_state)
        self.measured_bits[-1] = measured_bit
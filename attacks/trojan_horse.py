"""L'attaque trojan horse repose sur le fait d'emttre un faisceau lumineux vers le récepteur """

from utils.colors import bcolors
from intercept.factory import Intercept
from components.receiver import Receiver 
import qutip
from random import randint as rng

class TrojanHorse(Intercept):
    
    def __init__(self, apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob):
        print(bcolors.OKCYAN + "[ATTACK TROJAN HORSE] ..." + bcolors.ENDC)
        self.bob = bob
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)

    def get_cible_basis(self) -> int:
        if(len(self.bob.chosen_bases) == 0):
            return rng(0,1)
        return self.bob.chosen_bases[-1]
    
    def receive_qubit(self, sent_state : qutip.Qobj):
        with self._lock:
            if(self.qubit_received == True):
                self.already_receive_photon()
            else:
                # Eve mesure dans la base de Bob (trojan horse) : trigger_apd
                # mesure sent_state dans chosen_bases[-1] et renvoie le bit.
                chosen_basis = self.get_cible_basis()
                self.chosen_bases.append(chosen_basis)

                measured_bit = self.trigger_apd(sent_state)
                self.measured_bits.append(measured_bit)

                # Comme la base est celle de Bob, réémettre l'état mesuré
                # n'introduit aucune erreur : l'attaque reste indétectable.
                resent_qubit = self.STATES[(measured_bit, chosen_basis)]
                self.send_qubit(resent_qubit)

                self.qubit_received = True
                self.received_qubit_count += 1
                #if self.received_qubit_count == self.message_size:
                #    self.close_communication()

    def emit_qubit(self, bit : int):
        if self.sent_qubit_count == 0:
            self.communication_in_progress = True
        qubit = self.STATES[(bit, self.get_cible_basis())]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        if self.sent_qubit_count == self.message_size:
            self.communication_in_progress = False
            self.communication_finished.set()   # unblock anyone waiting

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
                chosen_basis = self.get_cible_basis()
                basis_state_0 = self.STATES[(0, chosen_basis)]
                basis_state_1 = self.STATES[(1, chosen_basis)]

                measured_bit = qutip.measurement.measure(
                    sent_state, [qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)]
                )[0]

                self.chosen_bases.append(chosen_basis)
                self.measured_bits.append(measured_bit)
                self.trigger_apd(measured_bit)

                resent_qubit = self.STATES[(measured_bit, chosen_basis)]

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
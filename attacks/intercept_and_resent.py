import qutip
from random import randint as rng
from utils.colors import bcolors
from intercept.factory import Intercept

class InterceptAndResent(Intercept):

    def __init__(self, apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob):
        print(bcolors.OKCYAN + "[CLASSIC ATTACK INTERCEPT AND RESENT] ..." + bcolors.ENDC)
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)


    # Appelée juste après chaque tick. Une base est tirée au hasard et le photon
    # est mesuré dans cette base. Base ET bit sont enregistrés ensemble.
    def receive_qubit(self, sent_state : qutip.Qobj):
        with self._lock:
            if(self.qubit_received == True):
                self.already_receive_photon()
            else:
                chosen_basis = rng(0, 1)
                basis_state_0 = self.STATES[(0, chosen_basis)]
                basis_state_1 = self.STATES[(1, chosen_basis)]

                measured_bit = qutip.measurement.measure(
                    sent_state, [qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)]
                )[0]

                self.chosen_bases.append(chosen_basis)
                self.measured_bits.append(measured_bit)
                self.trigger_apd(measured_bit)

                # Intercept-resend : on réémet vers Bob l'état qui correspond
                # exactement à ce qu'Eve a mesuré (bit mesuré, base de mesure).
                resent_qubit = self.STATES[(measured_bit, chosen_basis)]

                self.qubit_received = True

    def emit_qubit(self, bit : int):
        qubit = self.STATES[(bit, self.chosen_bases[len(self.chosen_bases)-1])]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1
import qutip
from random import randint as rng
from utils.colors import bcolors
from intercept.factory import Intercept

class InterceptAndResent(Intercept):

    def __init__(self, apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob):
        print(bcolors.OKCYAN + "[CLASSIC ATTACK INTERCEPT AND RESENT] ..." + bcolors.ENDC)
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)


    # Appelée juste après chaque tick. Une base est tirée au hasard et le photon
    # est mesuré une seule fois dans cette base (via trigger_apd), puis Eve
    # réémet vers Bob l'état correspondant.
    def receive_qubit(self, qubit : qutip.Qobj):
        with self._lock:
            if(self.qubit_received == True):
                self.already_receive_photon()
            else:
                # Eve choisit sa base au hasard. trigger_apd mesure le qubit
                # dans cette base (chosen_bases[-1]) et déclenche l'APD d'Eve.
                chosen_basis = rng(0, 1)
                self.chosen_bases.append(chosen_basis)

                measured_bit = self.trigger_apd(qubit)

                # Intercept-resend : on réémet vers Bob l'état qui correspond
                # exactement à ce qu'Eve a mesuré (bit mesuré, base de mesure).
                resent_qubit = self.STATES[(measured_bit, chosen_basis)]
                self.emit_qubit(resent_qubit)

                self.qubit_received = True

    # Réémet vers Bob l'état reconstruit par Eve (from_eve=True côté canal).
    def emit_qubit(self, qubit : qutip.Qobj):
        self.send_qubit(qubit)
        self.sent_qubit_count += 1
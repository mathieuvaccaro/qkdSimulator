import qutip
from random import randint as rng
from utils.colors import bcolors
from intercept.factory import Intercept


# Attaque "intercept and resend".
#
# Eve mesure chaque qubit d'Alice dans une base tirée au hasard, puis réémet
# vers Bob l'état correspondant exactement à ce qu'elle a mesuré.
#
# Toute l'infrastructure (STATES, apds, compteurs, verrous, canal...) est fournie
# par la classe de base Intercept ; on ne surcharge ici que le comportement propre
# à l'attaque : receive_qubit (mesure/réémission) et emit_qubit.
class InterceptAndResent(Intercept):

    # Appelée juste après chaque tick. Une base est tirée au hasard et le photon
    # est mesuré dans cette base. Base ET bit sont enregistrés ensemble.
    def receive_qubit(self, sent_state : qutip.Qobj):
        with self._lock:
            print(bcolors.OKGREEN + "HEHE" + bcolors.ENDC)
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
                self.received_qubit_count += 1
                if self.received_qubit_count == self.message_size:
                    self.close_communication()

    def emit_qubit(self, bit : int):
        if self.sent_qubit_count == 0:
            self.communication_in_progress = True
        qubit = self.STATES[(bit, self.chosen_bases[len(self.chosen_bases)-1])]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        if self.sent_qubit_count == self.message_size:
            self.communication_in_progress = False
            self.communication_finished.set()   # unblock anyone waiting
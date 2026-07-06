import time
import qutip
from random import randint as rng

import settings
from utils.colors import bcolors


#████  █████  ███  ████  ███ █   █  ███      ████ █████  ███  █████ ███  ███  █   █
#█   █ █     █   █ █   █  █  ██  █ █        █     █     █       █    █  █   █ ██  █
#████  ████  █████ █   █  █  █ █ █ █  ██     ███  ████  █       █    █  █   █ █ █ █
#█  █  █     █   █ █   █  █  █  ██ █   █        █ █     █       █    █  █   █ █  ██
#█   █ █████ █   █ ████  ███ █   █  ███     ████  █████  ███    █   ███  ███  █   █

# Reception side of the interceptor: it reads (measures) the qubits emitted by
# the sender. Attributes used here (STATES, lock, counters, apds...) are created
# by the factory (see intercept.factory).
class ReceptionMixin:

    # Called on every tick. We wait tolerance_message_not_receive ms;
    # if "qubit_received" is still False, the qubit was lost.
    # We then append a -1 marker to BOTH lists to stay aligned.
    def detect_lost_qubit(self):
        time.sleep(settings.tolerance_message_not_receive / 1000)
        with self._lock:
            if self.qubit_received == False:
                self.measured_bits.append(-1)
                self.chosen_bases.append(-1)  # keep basis <-> bit alignment
                self.received_qubit_count += 1
                if self.received_qubit_count == self.message_size:
                    self.close_communication()
            self.qubit_received = False

    # Called when receiver get more than one photon for a detection
    def already_receive_photon(self):
        self.nb+=1
        pass

    # Called right after each tick. A basis is drawn at random and the
    # photon is measured in that basis. Basis AND bit are recorded together.
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

                # Intercept-resend: resend to Bob the state that matches exactly
                # what Eve measured (measured bit, measurement basis).
                resent_qubit = self.STATES[(measured_bit, chosen_basis)]

                self.qubit_received = True
                self.received_qubit_count += 1
                if self.received_qubit_count == self.message_size:
                    self.close_communication()

    def close_communication(self):
        self.communication_finished.set()  # unblock anyone waiting
        self.clk.stop()

    # Fires the matching APD (simulation side effect).
    def trigger_apd(self, measured_bit : int):
        if measured_bit == 0:
            self.apd0.receive_photon()
        elif measured_bit == 1:
            self.apd1.receive_photon()
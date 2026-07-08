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
        if(self.finished == False):
            with self._lock:
                if self.qubit_received == False:
                    self.measured_bits.append(-1)
                    self.chosen_bases.append(-1)  # keep basis <-> bit alignment
                    self.received_qubit_count += 1
                    #if self.received_qubit_count == self.message_size:
                    #    self.close_communication()
                self.qubit_received = False

    # Called when receiver get more than one photon for a detection
    def already_receive_photon(self):
        self.nb+=1
        pass

#    def get_cible_basis(self) -> int:
#        if(len(self.bob.chosen_bases) == 0):
#            return rng(0,1)
#        return self.bob.chosen_bases[-1]

    # Called of each tick
    def prepare_bases(self, init = False):
        # Cette fonction tourne grace a la clock mais est activé grace a "init"
        
        if(self.received_qubit_count < self.message_size):
            chosen_basis = rng(0, 1)
            basis_state_0 = self.STATES[(0, chosen_basis)]
            basis_state_1 = self.STATES[(1, chosen_basis)]
            self.chosen_bases.append(int(chosen_basis))

    # Called right after each tick. A basis is drawn at random and the
    # photon is measured in that basis. Basis AND bit are recorded together.
    def receive_qubit(self, sent_state : qutip.Qobj):
         with self._lock:            
            if(self.received_qubit_count <= self.message_size):
                if(self.qubit_received == True):
                    self.already_receive_photon()
                else:
                    # Measure the qubit in the chosen basis
                    if(len(self.chosen_bases) == 0):
                        return
                    
                    basis_state_0 = self.STATES[(0, self.chosen_bases[-1])]
                    basis_state_1 = self.STATES[(1, self.chosen_bases[-1])]
                    measured_bit = qutip.measurement.measure(sent_state,[qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)])[0]

                    # We record basis + bit atomically, in the same block.
                    # The APD call is kept for simulation fidelity, but the bit
                    # feeding the key comes straight from the measurement,
                    # which removes the race with the asynchronous add_bits callback.
                    self.measured_bits.append(measured_bit)
                    self.trigger_apd(measured_bit)

                    self.qubit_received = True
                    self.received_qubit_count += 1

                    #if self.received_qubit_count == self.message_size:
                    #    self.close_communication()
            else:
                self.finished = True

    #def close_communication(self):
    #    self.communication_finished.set()  # unblock anyone waiting
    #    self.clk.stop()

    # Fires the matching APD (simulation side effect).
    def trigger_apd(self, measured_bit : int):
        if measured_bit == 0:
            self.apd0.receive_photon()
        elif measured_bit == 1:
            self.apd1.receive_photon()
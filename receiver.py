import qutip
from random import randint as rng
from random import sample as rng_s
import apd
from utils.colors import bcolors
import clock
import time
import settings
import numpy as np
import threading
import quantum_canal
import protocols.protocol_manager as pm


class Receiver:

    def __init__(self, apd0: apd.Apd, apd1: apd.Apd, quantum_channel, clk: clock.Clock):
        self.apd0 = apd0
        self.apd1 = apd1
        self.quantum_channel = quantum_channel
        self.clk = clk
        self.clk.subscribe(self.detect_lost_qubit)

        # One basis and one bit per tick, kept aligned index by index
        self.chosen_bases = []
        self.measured_bits = []

        self.qubit_received = False
        self.message_size = settings.message_size  # Number of bits per QKD run
        self.received_qubit_count = -1  # bit index, -1 because the sender starts at 0
        self.communication_finished = threading.Event()

        # Guards the attributes shared between the clock thread,
        # the lost-qubit detector and the APD callback
        self._lock = threading.Lock()

        # Get state by protocol
        self.STATES = pm.get_states()

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

    # Called right after each tick. A basis is drawn at random and the
    # photon is measured in that basis. Basis AND bit are recorded together.
    def receive_qubit(self, sent_state : qutip.qobj):


        with self._lock:
            if self.received_qubit_count == 0:
                print(bcolors.OKBLUE + "[RECEIVER] - START OF COMMUNICATION" + bcolors.ENDC)

            chosen_basis = rng(0, 1)
            basis_state_0 = self.STATES[(0, chosen_basis)]
            basis_state_1 = self.STATES[(1, chosen_basis)]

            # Measure the qubit in the chosen basis
            measured_bit = qutip.measurement.measure(sent_state,[qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)])[0]

            # We record basis + bit atomically, in the same block.
            # The APD call is kept for simulation fidelity, but the bit
            # feeding the key comes straight from the measurement,
            # which removes the race with the asynchronous add_bits callback.
            self.chosen_bases.append(chosen_basis)
            self.measured_bits.append(measured_bit)
            self.trigger_apd(measured_bit)

            self.qubit_received = True
            self.received_qubit_count += 1

            if self.received_qubit_count == self.message_size:
                self.close_communication()

    def close_communication(self):
        print(bcolors.OKBLUE + "[RECEIVER] - END OF COMMUNICATION" + bcolors.ENDC)
        #self.communication_in_progress = False
        self.communication_finished.set()  # unblock anyone waiting
        self.clk.stop()

    # Fires the matching APD (simulation side effect).
    def trigger_apd(self, measured_bit : int):
        if measured_bit == 0:
            self.apd0.receive_photon()
        elif measured_bit == 1:
            self.apd1.receive_photon()

    def read_value(self, value : int):
        # print(bcolors.OKGREEN +f"Photon correctly detected ({value})!" + bcolors.ENDC)
        pass
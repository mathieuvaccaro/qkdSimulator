import qutip
from random import randint as rng
from random import sample as rng_s
import components.apd as apd
from utils.colors import bcolors
import components.clock as clock
import time
import settings
import numpy as np
import threading
import components.quantum_canal as quantum_canal
import protocols.protocol_manager as pm


class Receiver:

    def __init__(self, apd0: apd.Apd, apd1: apd.Apd, quantum_channel, clk: clock.Clock):
        self.apd0 = apd0
        self.apd1 = apd1
        self.quantum_channel = quantum_channel
        self.clk = clk
        # Les souscriptions à l'horloge sont faites explicitement par le manager,
        # dans un ordre garanti : prepare_bases (choix de la base) AVANT emit_qubit
        # (émission + réception), puis detect_lost_qubit.
        self.finished = False
        
        # One basis and one bit per tick, kept aligned index by index
        self.chosen_bases = []
        self.measured_bits = []

        self.qubit_received = False
        self.message_size = settings.message_size  # Number of bits per QKD run
        self.received_qubit_count = 0
        self.communication_finished = threading.Event()

        # Guards the attributes shared between the clock thread,
        # the lost-qubit detector and the APD callback
        self._lock = threading.Lock()

        # Get state by protocol
        self.STATES = pm.get_states()

    def detect_lost_qubit(self):
        time.sleep(settings.tolerance_message_not_receive / 1000)
        if(self.finished == False):
            with self._lock:
                if self.qubit_received == False:
                    self.measured_bits.append(-1)
                    self.received_qubit_count += 1
                    if self.received_qubit_count == self.message_size:
                        self.close_communication()
                        self.communication_finished.set()
                self.qubit_received = False

    # Called when receiver get more than one photon for a detection
    def already_receive_photon(self):
        #print(bcolors.WARNING + "Un photon a déjà était reçu, on le jete" + bcolors.ENDC)
        pass

    def prepare_bases(self):
        if(self.received_qubit_count < self.message_size):
            self.chosen_bases.append(rng(0, 1))

    def receive_qubit(self, sent_state : qutip.qobj):
        with self._lock:
            if(self.received_qubit_count < self.message_size):
                if(self.qubit_received == True):
                    self.already_receive_photon()
                else:
                    # Measure the qubit in the chosen basis
                    if(len(self.chosen_bases) == 0):
                        return
                    
                    basis_state_0 = self.STATES[(0, self.chosen_bases[-1])]
                    basis_state_1 = self.STATES[(1, self.chosen_bases[-1])]
                    measured_bit = qutip.measurement.measure(sent_state,[qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)])[0]

                    self.measured_bits.append(measured_bit)
                    self.trigger_apd(measured_bit)

                    self.qubit_received = True
                    print(f"Reception : {self.received_qubit_count}")
                    self.received_qubit_count += 1
                    
            print(f"{self.received_qubit_count} vs {self.message_size}")
            if self.received_qubit_count == self.message_size:
                self.close_communication()
                self.communication_finished.set()   # unblock anyone waiting


    def close_communication(self):
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
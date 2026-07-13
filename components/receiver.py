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

"""La réception elle-même fonctionne de manière asynchrone grâce a "quantum_canal.py" qui appelle la fonction "receiver_qubit" directement.
Cependant le choix de la base se fait en amont de manière synchrone (donc au même instant précisement que la création du qubit par sender.py)
Afin de détecter si le bit est perdu, une fonction "detect_lost_qubit" se lance de manière synchrone en attendant un temps tolerance_message_not_receive ms. Si aucun bit n'est recu durant cette période, le qubit est considérer comme perdu (snif)
"""

class Receiver:

    def __init__(self, apd0: apd.Apd, apd1: apd.Apd, quantum_channel, clk: clock.Clock):
        """Initialise le receveur (Bob) avec ses deux apd, le canal quantique et la clock commune

        Args:
            apd0 (apd.Apd): apd associé au bit 0
            apd1 (apd.Apd): apd associé au bit 1
            quantum_channel: canal quantique par lequel arrivent les qubits
            clk (clock.Clock): clock commune de synchronisation
        """
        self.apd0 = apd0
        self.apd1 = apd1
        self.quantum_channel = quantum_channel
        self.clk = clk
        self.finished = False
        
        self.chosen_bases = []
        self.measured_bits = [-1] * settings.message_size
        self.pending_index = None  # index du tick du qubit en cours de mesure

        self.qubit_received = False
        self.qubit_analyzed = False
        self.message_size = settings.message_size  # Nombre de qubit par QKD
        self.received_qubit_count = 0
        self.communication_finished = threading.Event()

        self._lock = threading.Lock() # Just un mutex

        self.STATES = pm.get_states() # Récupère le state en fonction du protocol (pour l'instant on a que BB84)

    def detect_lost_qubit(self):
        time.sleep(settings.tolerance_message_not_receive / 1000)
        if(self.finished == False):
            with self._lock:
                if self.qubit_analyzed == False:
                    # Perte : soit le photon n'est jamais arrivé, soit l'APD ne l'a pas détecté
                    if len(self.chosen_bases) > 0:
                        self.chosen_bases[-1] = -1
                self.received_qubit_count += 1          # <- une seule fois par tick
                if self.received_qubit_count == self.message_size:
                    self.close_communication()
                self.qubit_received = False
                self.qubit_analyzed = False


    def already_receive_photon(self):
        """Ca arrive qu'on recoit plusieurs photons, dans ce cas, le comportement du receveur peut varier"""
        #print(bcolors.WARNING + "Un photon a déjà était reçu, on le jete" + bcolors.ENDC)
        pass

    def prepare_bases(self):
        """On prépare chaque base en amont avant la réception du bit"""
        if(self.received_qubit_count < self.message_size):
            self.chosen_bases.append(rng(0, 1))

    def receive_qubit(self, qubit : qutip.qobj):
        """Cette fonction est appelé par le canal quantique lorsuqe un qubit est arrivé

        Args:
            qubit (qutip.qobj): qubit recu par le canal.
        """        
        with self._lock:
            if(self.received_qubit_count < self.message_size):
                if(self.qubit_received == True):
                    self.already_receive_photon()
                else:
                    # On mémorise le tick de ce qubit pour que read_value (appelé
                    # par le thread de l'APD) écrive le bit dans le bon slot.
                    self.pending_index = len(self.chosen_bases) - 1
                    self.trigger_apd(qubit)

                    self.qubit_received = True
                    #self.received_qubit_count += 1
            if self.received_qubit_count == self.message_size:
                self.close_communication()

    def close_communication(self):
        """Lorsqu'on close la communication, on fait deux choses :
            - on envoie l'information au manager.py de continuer sa vie
            - on stoppe la clock (parce qu'on est le receptuer et donc la dernière étape de la QKD)
        """
        self.communication_finished.set()
        self.clk.stop()

    def trigger_apd(self, qubit : qutip.qobj):
        """En pratique, les qubits sont envoyé dans un analyseur qui va transmettre le photon a un APD ou l'autre. Ici l'analyseur est entièrement simulé
        fictivement, dans le sens ou c'est juste une mesure qutip. Ensuite le photon est transmis a l'apd liée

        Args:
            qubit (qutip.qobj): qubit recu par le canal.
        """        

        # Measure the qubit in the chosen basis
        if(len(self.chosen_bases) == 0):
            return
        
        basis_state_0 = self.STATES[(0, self.chosen_bases[-1])]
        basis_state_1 = self.STATES[(1, self.chosen_bases[-1])]
        measured_bit = qutip.measurement.measure(qubit,[qutip.ket2dm(basis_state_0), qutip.ket2dm(basis_state_1)])[0]

        if measured_bit == 0:
            self.apd0.receive_photon()
        elif measured_bit == 1:
            self.apd1.receive_photon()


    def read_value(self, value : int):
        """Cette fonction est appelé par l'APD lui même qui sert de gestionnaire avant de faire une action. Ici c'est juste ajouter un élément dans un tablea

        Args:
            value: Bit (binaire) final lu par l'apd

        """

        # On écrit dans le slot du tick mémorisé (pending_index) cela pemert de toujours lire malgrès le possible décalage de temps
        idx = self.pending_index
        self.qubit_analyzed = True
        if idx is not None and 0 <= idx < len(self.measured_bits):
            self.measured_bits[idx] = value
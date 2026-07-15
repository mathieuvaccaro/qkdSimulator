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
import random
import protocols.protocol_manager as pm

"""La réception elle-même fonctionne de manière asynchrone grâce a "quantum_canal.py" qui appelle la fonction "receiver_qubit" directement.
Cependant le choix de la base se fait en amont de manière synchrone (donc au même instant précisement que la création du qubit par sender.py)
Afin de détecter si le bit est perdu, une fonction "detect_lost_qubit" se lance de manière synchrone en attendant un temps tolerance_message_not_receive ms. Si aucun bit n'est recu durant cette période, le qubit est considérer comme perdu (snif)
Il n'y a pas de gestion de double click
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
        self.value_analyzed = [] # Bits déjà analysé dans le cas d'un double click event
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
                # On mémorise le tick de ce qubit pour que read_value (appelé
                # par le thread de l'APD) écrive le bit dans le bon slot.
                self.pending_index = len(self.chosen_bases) - 1
                self.trigger_apd(qubit)

                self.qubit_received = True
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
        A ce stage on a pas gérer les double clicks, il le seront dans le fonction "addBitToKey()". On se contente d'ajouter dans un tableau
        Args:
            value: Bit (binaire) final lu par l'apd
        """

        # On ajoute la valeur dans la liste
        self.value_analyzed.append(value)
        self.qubit_analyzed = True

    def addBitToKey(self):
        """Cette fonction est appelé de manière synchrone et permet d'ajouter le bit a la clé.
        - Si il y a qu'un seul bit qui à été mesuré, il est simplement ajouté et l'index est incrémenter
        - Si il y a aucun bit ajouté, l'index est incrémenter permettant de laisser le -1
        - Si il y a plusieurs bits, le choix dépend du choix du paramètre dans settings.py. Soit les bits sont jetés (dangeureux) soit les bits sont choisi aléatoiremeent (pas dangeureux)
        """
        # La communication n'a pas encore commencé
        if(self.pending_index == None):
            return

        # Aucun bit n'a été analysé
        if(len(self.value_analyzed) == 0):
            pass

        # Un seul bit a été détecte
        elif(len(self.value_analyzed) == 1):
            self.measured_bits[self.pending_index] = self.value_analyzed[0]

        # Plusieurs bits ont été analysé
        else:
            if(settings.many_clicks_gestion == "THROWS"):
                self.chosen_bases[-1] = -1
                pass
            elif(settings.many_clicks_gestion == "RANDOM"):
                r = random.randint(0, len(self.value_analyzed)-1)
                self.measured_bits[self.pending_index] = self.value_analyzed[r]
            else:
                raise Exception(f"[ERROR] - Paramètre {settings.many_clicks_gestion} non reconnu !")
        # Dans tous les cas on incrémente le compteur ;)
        self.pending_index+=1
        # Et on reset la liste des valeurs
        self.value_analyzed.clear()
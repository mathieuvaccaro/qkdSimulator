import itertools
import time

import qutip

from intercept.factory import Intercept
from components.apd import Apd
from components.quantum_canal import QuantumCanal
from components.clock import Clock
from components.sender import Sender
from components.receiver import Receiver
import settings
from utils.colors import bcolors
from utils.progress_bar import progress_bar


class CorrelationTime(Intercept):
    # * docstring entièrement réécrite ci-dessous (vs original)
    """Attaque statistique par observation du temps (exploitation du dead time des APD de Bob).

    Principe : les APD de Bob ont un dead time non nul (settings.dead_time_min/max, en ms) nétemment
    supérieur à l'intervalle d'émission. Après une détection sur un détecteur (bit 0 OU bit 1),
    ce détecteur reste aveugle pendant tout son dead time. Par conséquent, deux détections
    successives séparées par un temps inférieur au dead time NE PEUVENT PAS provenir du même
    détecteur : elles portent donc forcément deux bits opposés.

    Eve est passive : elle se contente d'horodater chaque qubit puis de le réémettre
    inchangé vers Bob (le QBER n'augmente pas, l'attaque est indétectable). Après le sifting
    public, elle sait quels slots Bob a détectés (bob_bases[i] != -1) et lesquels ont été
    conservés (alice_bases[i] == bob_bases[i]). En comparant les horodatages des détections
    successives au dead time minimal, elle reconstruit des "chaînes" de bits alternés.

    À l'intérieur d'une chaîne, tous les bits sont connus à une inversion globale près (2 candidats).
    eve_sifting renvoie donc la liste des combinaisons possibles de la clé siftée ; manager.py
    retient la meilleure (borne supérieure de la connaissance d'Eve).

    Attention : l'énumération n'est pas bornée. Avec C chaînes, eve_sifting construit exactement
    2^C clés candidates, on suppose donc ici une clé de petite taille (settings.message_size).

    QBER Estimé : 0%
    Connaissance de clé : 100% dans le meilleur cas (toutes les orientations étant énumérées,
        la vraie clé siftée figure forcément parmi les candidates)
    Détectable : Non

    Remarque : on suppose (comme dans le rapport) qu'Eve connaît la durée du dead time des APD.

    Args:
        Intercept (_type_): Héritage de intercept (factory.py)
    """

    def __init__(self, apdEve0 : Apd, apdEve1 : Apd , quantum_canal : QuantumCanal, commune_clk : Clock, alice : Sender, bob : Receiver):
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk, alice, bob)
        self.array_time = [None] * self.message_size   
        self.slot = 0
        self.test = 0

    def receive_qubit(self, qubit : qutip.Qobj):
        """Appelée par le canal quantique à l'arrivée d'un qubit émis par Alice.

        Eve enregistre simplement l'instant d'arrivée du slot courant, puis transmet le qubit.

        Args:
            qubit (qutip.Qobj): qubit reçu par le canal.
        """
        with self._lock:
            # Check au cas ou il y a plusieurs qubit de recu, qu'on garde qu'un seul horodatage :)
            if self.slot < len(self.array_time) and not self.qubit_received:
                self.array_time[self.slot] = time.perf_counter_ns()
                self.qubit_received = True 
            self.emit_qubit(qubit)

    def emit_qubit(self, qubit : qutip.Qobj):
        """Réémet vers Bob le qubit intercepté, sans le modifier.

        Args:
            qubit (qutip.Qobj): qubit à émettre sur le canal.
        """
        self.send_qubit(qubit)
        self.sent_qubit_count += 1

    def detect_lost_qubit(self):
        """Appelée une fois par tick de la clock commune.

        On redéfinit cette fonction (au lieu d'utiliser celle du ReceptionMixin) afin de
        garder un index de slot fiable : on avance d'exactement un slot par tick. Le qubit
        du slot, s'il existe, a déjà été reçu de façon synchrone pendant alice.emit_qubit
        (appelée plus tôt dans le même tick) ; aucune attente n'est donc nécessaire.
        """
        if self.finished == False: 
            with self._lock:
                self.qubit_received = False
                self.slot += 1
                if self.slot >= self.message_size:
                    self.finished = True

    def eve_sifting(self, alice_bases : list[int], bob_bases : list[int]) -> list[list[int]]:
        """Analyse a posteriori de l'attaque, à partir des bases publiques d'Alice et de Bob.

        1. Récupérer les slots détecté par bob
        2. Si l'écart entre deux réception est inférieur au dead time minimal, on en fait une chaine
        3. Enumérer toutes les possibilités à partir des chaines obtenues

        Args:
            alice_bases (list[int]): bases d'Alice révélées publiquement.
            bob_bases (list[int]): bases de Bob révélées publiquement (-1 = non détecté).

        Returns:
            list[list[int]]: liste des clés siftées candidates (même longueur que la clé siftée).
        """

        # 1- On récupere que les bits siftés
        detections = []
        for i in range(len(bob_bases)):   # On prends la base de bob en référence, mais les bse d'alice et bob sont censé être identique
            if bob_bases[i] != -1:
                detections.append((i, alice_bases[i] == bob_bases[i])) # On rajoute True/False, pour garder le temps écoulé en mémoire entre deux détection même si elle est éronnée

        # 2- Comme vu dans le rapport si le temps entre la récépeiton de deux bits consécutif est inférieur à deadtime_min,
        # c'est que les deux bits sont opposés
        attente = settings.dead_time_min * 1e6  # temps minimal du dead_time, on ne peux pas savoir en temps réel le dead time actuelle (conversion ms -> ns)
        chain_of = []  # index de chaîne pour chaque détection
        bit_of = []    # valeur relative (0/1) dans la chaîne, avant inversion globale
        current_chain = -1 
        prev_slot = None # Juste l'indice du slot précédent, pour rappel, les slots ne sont pas linéaires (1,2,3,4,...) il est donc nécessaire de le stocker
        for (slot, _) in detections:
            t = self.array_time[slot] # Récupérer le temps (epoch) de la détection 'slot'

            # Si le temps entre le slot précédent et celui actuel est plus bas que le dead time, alors on prends l'opposé du bit précédent
            if prev_slot is not None and t is not None and self.array_time[prev_slot] is not None and (t - self.array_time[prev_slot]) < attente:
                bit = 1 - bit_of[-1] # On prends l'opposé du dernier bit utilisé
            else:
                current_chain += 1 # Ajoute une chaine possible (sert aussi d'instnace)
                bit = 0 # Le bit 0 est choisi arbitrairemtn

            chain_of.append(current_chain)
            bit_of.append(bit)
            prev_slot = slot

        # 3- On ne veux garder seulement les bits siftés, donc on va reprendre la liste de base (1) 
        sifted = []
        for k in range(len(detections)):
            if detections[k][1]: # True -> Sifté, Flase -> Non sifté
                sifted.append((chain_of[k], bit_of[k]))

        # Cas vide (crash anticipée)
        if len(sifted) == 0:
            return [[]]

        # 4 - A ce niveau< sifted a des trous, on va lister directment toutes les chaines possible (de manière unique)
        chains_present = [] # 
        for (chain, _) in sifted:
            if chain not in chains_present:
                chains_present.append(chain)

        # Nous avons les différents flips, mais nous sommes parti du principe que toutes les séquence comemncent par 0
        # Ce n'est pas forcément les cas, il faut voir toutes les possibilités
        # Etant donné que nous n'avons pas accès a la clé depuis le point de vue de Eve, nous retournons la liste des
        # possibilités, c'est au manager de regarder si la clé est contenue.
        # Par exemple : Sifted = [(1, 0), (1, 1), (6, 0)] le résultat est [(0, 1, 0) ; (0, 1, 1) ; (1, 0, 0) ; (1, 0, 1)]
        
        # REMARQUE : Après quatre jours (soit quasiment 30h) de code a rester bloqué sur cette putain de section, j'ai craqué
        # La section suivante a donc été codée par Claude AI, Cordialement

        C = len(chains_present)
        resultats = []


        print("Elaboration de toutes les possibilités d'attaques, cela peut prendre du temps....")

        for n in range(2 ** C):

            progress_bar(n, 2 ** C)
            
            
            # 5a - Décoder n en un flip par chaine
            flip_par_chaine = {}
            for j in range(C):
                flip_par_chaine[chains_present[j]] = (n >> j) & 1  # bit j de n

            # 5b - Construire la clé candidate en reparcourant sifted
            cle = []
            for (chain, bit_relatif) in sifted:
                if flip_par_chaine[chain] == 1:
                    cle.append(1 - bit_relatif)  # inversion globale de la chaine
                else:
                    cle.append(bit_relatif)

            resultats.append(cle)


        return resultats

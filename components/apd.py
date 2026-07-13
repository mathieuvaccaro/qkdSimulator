import components.clock as clock  # We use clock.py
from utils.colors import bcolors
import random

"""
Un apd permet "simplement" la lecture d'un photon, il fonctionne d'une manière particulière (cf. rapport)
Pour faciliter la chose dans un programme python, nous avons approximé le circuit quanitque par un circuit électronique
"""

def approx_equal(x : float, y : float, tolerance=0.001) -> bool:
    """Une simple fonction auxiliaire permettant de savoir si deux nombre sont approximativement égaux

    Args:
        x (int): nombre 1
        y (int): nombre 2
        tolerance (float, optional): tolerance. Defaults to 0.001.

    Returns:
        bool: True si les nombres sont approximativement égaux, False sinon
    """    
    if x + y == 0:
        return abs(x - y) <= tolerance
    return abs(x - y) <= 0.5 * tolerance * abs(x + y)


class Apd:
    """Objets Apd

    Variables:
        linked_bit         : bit associé au détecteur (0 ou 1)
        breakdown_voltage  : V_br (in V)
        dead_time_min/_max          : dead time, en ms
        bias_voltage       : V_dc < V_br  /!\  (tension constante)
        gate_voltage       : tension ajouté durant le mode geiger
        gate_on_duration   : Durée (en ms) durant laquel la détection est Actif
        gate_off_duration  : Durée (en ms) durant laquel la détection est Inactif
        clock_period       : Clock commune

    Raises:
        ValueError: Renvoie une erreur si certaines conditions d'usage ne sont pas respectés
    """    

    def __init__(self, linked_bit, breakdown_voltage=7, dead_time_min=3, dead_time_max = 5,
                 bias_voltage=5, gate_voltage=5,
                 gate_off_duration=20, gate_on_duration=20, clock_period=10):

        # Geiger mode requires V_dc + V_gate STRICTLY above the breakdown voltage.
        if bias_voltage + gate_voltage <= breakdown_voltage:
            raise ValueError(
                "bias_voltage + gate_voltage doit etre > breakdown_voltage"
            )

        self.mode = "linear"
        self.bias_voltage = bias_voltage
        self.gate_voltage = gate_voltage
        self.breakdown_voltage = breakdown_voltage  # V_br (V)

        self.bit_received = False
        self.linked_bit = linked_bit

        self.dead_time_min = dead_time_min # in ms
        self.dead_time_max = dead_time_max # in ms

        self.gate_off_duration = gate_off_duration  # in ms
        self.gate_on_duration = gate_on_duration    # in ms

        self.voltage = self.bias_voltage  # instantaneous bias across the APD

        self.clock_period = clock_period  # in ms

        self.gate_open = False  # True while the detection window is open

        self.gate_timer = 0

        # dead time change a chaque photon recu
        # Si dead_time_elapsed >= dead_time -> la détection est actif
        # Si dead_time_elapsed <  dead_time -> la détection est inactif
        self.dead_time = round(random.uniform(self.dead_time_min, self.dead_time_max), 2)

        self.dead_time_elapsed = self.dead_time
        
    def set_parent(self, parent):
        """Défini le parent (le receveur) auquel l'apd transmet le bit détecté

        Args:
            parent: entité recevant les bits lus (Receiver ou intercepteur)
        """
        self.parent = parent

    def start_clock(self):
        """Création de la clock et abonnement des fonctions
        """        
        self.clk = clock.Clock(self.clock_period)
        self.clk.subscribe(self.update_gate)
        self.clk.subscribe(self.update_voltage)
        self.clk.subscribe(self.update_mode)
        self.clk.subscribe(self.update_dead_time)
        self.clk.start()

    def update_mode(self):
        """On va mettre à jour le mode en fonction du voltage actuelle. (indirectement, si la tension de gate à été ajouté ou non)
        """        
        self.mode = "geiger" if self.voltage > self.breakdown_voltage else "linear"

    def update_gate(self):
        """L'apd va s'activer uniquemnt durant une certaine période au moment de la détection souhaité
        time appartient [0, gate_on_duration[ -> Détection activé
        time appartient [gate_in_duration, on + off[ -> Détection désactive
        Cette fonction est appelé une fois par tick
        """        
        self.gate_timer += self.clock_period
        if self.gate_timer >= self.gate_on_duration + self.gate_off_duration:
            self.gate_timer = 0

        self.gate_open = self.gate_timer < self.gate_on_duration

    def update_voltage(self):
        """Mise à jour de la tension en fonction du mode de détection
        """        
        if self.gate_open:
            self.voltage = self.bias_voltage + self.gate_voltage
        else:
            self.voltage = self.bias_voltage

    def update_dead_time(self):
        """Mise à jour du dead_time, on va juste incrémenter un compteur a chaque tick 
        """        
        if self.dead_time_elapsed < self.dead_time:
            self.dead_time_elapsed += self.clock_period

    def receive_photon(self):
        """Réception + détection du photon. Appelé depuis la classe reception.
        La détection utilise l'état de la gate à l'instant exact de la réception.
        """
        if(self.gate_open and self.mode == "geiger" and self.dead_time_elapsed >= self.dead_time):
            self.dead_time_elapsed = 0  # start the dead time
            self.dead_time = round(random.uniform(self.dead_time_min, self.dead_time_max), 2) # Mise a jour du nouveau dead time

            self.parent.read_value(self.linked_bit)

    def run(self):
        """Lance la simulation de l'apd en démarrant sa clock interne
        """
        self.start_clock()
import threading

import settings
import components.clock as clock
import protocols.protocol_manager as pm
from components.apd import Apd

from intercept.reception import ReceptionMixin
from intercept.sending import SendingMixin


# ███  █      ███  ████   ███  █         ████ █████  ███  █████ ███  ███  █   █
#█     █     █   █ █   █ █   █ █        █     █     █       █    █  █   █ ██  █
#█  ██ █     █   █ ████  █████ █         ███  ████  █       █    █  █   █ █ █ █
#█   █ █     █   █ █   █ █   █ █            █ █     █       █    █  █   █ █  ██
# ███  █████  ███  ████  █   █ █████    ████  █████  ███    █   ███  ███  █   █

# C'est déjà assez compliqué, pour le coup je vais commenter en francais
# L'interception fonctionne par un objet avec héritage, ici c'est le factory (la création de l'objet)
# Pour cela on a une partie sending et une partie récéption
class Intercept(ReceptionMixin, SendingMixin):

    message_size = settings.message_size

    def __init__(self, apd0: Apd, apd1: Apd, quantum_channel, clk: clock.Clock, Alice = None, Bob = None):
        # GLOBAL
        self.quantum_channel = quantum_channel
        self.chosen_bases = []
        self.measured_bits = []
        self.clk = clk
        self.clk.subscribe(self.detect_lost_qubit)
        self.communication_finished = threading.Event()
        self.STATES = pm.get_states()
        self.finished = False

        self.nb = 0
        # (only) READING
        self.apd0 = apd0
        self.apd1 = apd1
        self.qubit_received = False
        self.message_size = settings.message_size  # Number of bits per QKD run
        self.received_qubit_count = -1  # bit index, -1 because the sender starts at 0
        self._lock = threading.Lock()

        # (only) SENDING
        self.sent_qubit_count = 0
        self.communication_in_progress = False


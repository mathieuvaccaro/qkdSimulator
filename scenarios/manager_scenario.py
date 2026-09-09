"""
Sert de point d'entrée aux test
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import settings
import manager
from manager import QkdResult

_ATTACK_FLAGS = ("INTERCEPT_AND_RESENT", "PNS", "TROJAN_HORSE", "DOUBLE_CLICK_EVENT", "TIME_CORRELATION")


def run_qkd(*, attack=None, message_size=settings.message_size, message_interval=settings.message_interval,
            average_emitted_photon=-1, perfect_apd=True, gate_off_duration = 0, dead_time_min = 2, dead_time_max = 6, gate_on_duration = 20,
            bit_loss=0.0, bit_flip=0.0, many_clicks_gestion="THROWS") -> QkdResult:
    """Lance un échange QKD complet et renvoie un `QkdResult`.

    Args:
        attack: None, "intercept_and_resent", "PNS", "TrojanHorse" etc.
        message_size: nombre de qubits envoyés par Alice.
        message_interval: période de la clock (ms).
        average_emitted_photon: moyenne de la loi de Poisson de la source.
            -1 = exactement 1 photon à chaque fois (source idéale).
        perfect_apd: True = APD parfait ; False = configuration réaliste (avec pertes).
        bit_loss / bit_flip: bruit du canal quantique, en % (0 à 100).
        timeout: sécurité anti-blocage, en secondes.

    Returns:
        QkdResult: clés d'Alice/Bob/Eve et métriques (QBER, connaissance d'Eve...).
    """

    settings.message_size = message_size
    settings.message_interval = message_interval
    settings.tolerance_message_not_receive = message_interval - 0.2
    settings.average_emitted_photon = average_emitted_photon
    settings.perfect_apd_bob = perfect_apd
    settings.quantum_canal_bit_loss = bit_loss
    settings.quantum_canal_bit_flip = bit_flip
    settings.progress_bar = False  # pas de barre de progression pendant les tests

    settings.gate_off_duration = gate_off_duration
    settings.gate_on_duration = gate_on_duration
    settings.dead_time_max = dead_time_max
    settings.dead_time_min = dead_time_min

    settings.many_clicks_gestion = many_clicks_gestion

    for flag in _ATTACK_FLAGS:
        setattr(settings, flag, flag == attack)

    return manager.run_communication()

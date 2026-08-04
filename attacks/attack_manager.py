import settings
from attacks.intercept_and_resent import InterceptAndResent
from attacks.PNS import Pns
from attacks.trojan_horse import TrojanHorse
from attacks.double_click_event import DoubleClickEvent
from attacks.correlations_time import CorrelationTime

# Liste des attaques disponible avec les classes héritant
ATTACK_REGISTRY = [
    ("INTERCEPT_AND_RESENT", InterceptAndResent),
    ("PNS", Pns),
    ("TROJAN_HORSE", TrojanHorse),
    ("DOUBLE_CLICK_EVENT", DoubleClickEvent),
    ("TIME_CORRELATION", CorrelationTime)
]


def get_active_attack():
    """Permet de récuperer l'attaque active d'après le fichier settings.py
    Si aucune attaque n'est activé, retourne None

    Returns:
        type | None: classe de l'attaque active à instancier, None si aucune attaque n'est activée
    """
    for flag, attack_cls in ATTACK_REGISTRY:
        if getattr(settings, flag, False):
            return attack_cls
    return None

def get_specific_attack(attack):
    for flag, attack_cls in ATTACK_REGISTRY:
        if flag == attack:
            return attack_cls
    return None
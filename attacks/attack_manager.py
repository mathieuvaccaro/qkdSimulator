import settings
from attacks.intercept_and_resent import InterceptAndResent
from attacks.PNS import Pns

# Liste des attaques disponible avec les classes héritant
ATTACK_REGISTRY = [
    ("intercept_and_resent", InterceptAndResent),
    ("PNS", Pns),
]


# Renvoie la classe d'attaque active d'après les flags de settings,
# ou None si aucune attaque n'est activée (Eve absente du canal).
def get_active_attack():
    for flag, attack_cls in ATTACK_REGISTRY:
        if getattr(settings, flag, False):
            return attack_cls
    return None
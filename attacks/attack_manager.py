from attacks import PNS
import settings
from attacks.intercept_and_resent import InterceptAndResent


# Registre des attaques disponibles.
#
# Chaque attaque est une sous-classe de Intercept, associée au flag de settings.py
# qui l'active. L'ordre définit la priorité si plusieurs flags étaient à True.
#
# Pour ajouter une attaque :
#   1. créer une sous-classe de Intercept dans attacks/ (surcharger receive_qubit
#      / emit_qubit),
#   2. ajouter son flag dans settings.py,
#   3. l'enregistrer ci-dessous.
ATTACK_REGISTRY = [
    ("intercept_and_resent", InterceptAndResent),
    ("pns", PNS),
]


# Renvoie la classe d'attaque active d'après les flags de settings,
# ou None si aucune attaque n'est activée (Eve absente du canal).
def get_active_attack():
    for flag, attack_cls in ATTACK_REGISTRY:
        if getattr(settings, flag, False):
            return attack_cls
    return None
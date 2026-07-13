"""L'attaque trojan horse repose sur le faite que Eve peut envoyer un faisceau lumineux intense sur l'émetteur d'Alice (contenant la base d'encodage). 
    De par la loi de Fresnel, une partie de la lumière est réfléchi en contenant l'information de la base utilisant pour la lecture

    Remarque : Il est difficile (même impossible) d'envoyer un faisceau lumineux dans un émetteur en simulant un programme Python. il s'agit donc 
    d'une simulation brève en supposant qu'on y arrive.

    QBER Estimé : 0%
    Clé Estimé : 100%
    Détectable : Non

    Args:
        Intercept (_type_): Héritage de factory.py dans intercept
"""

import pytest
from manager_test import run_qkd

ATTACK = "TrojanHorse"
TOLERANCE = 2 # Etant donné qu'il y a du bruit, on va tolérer quelques erreurs


@pytest.mark.parametrize("perfect_apd", [True, False])
def test_trojan_est_indetectable(perfect_apd):
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, perfect_apd=perfect_apd)
    assert r.n_errors() <= TOLERANCE, "l'attaque trojan ne doit pas créer d'erreur"

def test_trojan_eve_connait_toute_la_cle():
    """Eve connaît la quasi-totalité de la clé (~100 %)."""
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1)

    assert r.eve_knowledge() is not None
    assert r.eve_knowledge() >= 90, "Eve doit connaître la quasi-totalité de la clé (>90%)"


@pytest.mark.parametrize("moyenne", [0.3, 1.0, 2.0])
def test_trojan_reste_indetectable_avec_source_poisson(moyenne):
    """Même avec une source de Poisson (plus ou moins de photons), l'attaque
    reste sans erreur et Eve garde ~100 % de la clé.
    """
    r = run_qkd(attack=ATTACK, average_emitted_photon=moyenne)

    assert r.n_errors() <= TOLERANCE
    assert r.eve_knowledge() is not None
    assert r.eve_knowledge() >= 90

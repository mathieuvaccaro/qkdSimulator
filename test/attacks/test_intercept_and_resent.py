"""L'attaque intercept and resent et simplement "l'attaque par défaut". Eve arrive à se situer entre Alice et Bob sur le canla de communication
    Elle va se contenter de mesurer les qubits émis par Alice dans une base aléatoire, le ré-encoder et le transmettre à Bob.

    QBER Estimé : 25%
    Conaissance de clé : 50%
    Détectable : Oui
    Args:
        Intercept (_type_): Héritage de intercept (factory.py)
"""

import pytest
from manager_test import run_qkd

ATTACK = "intercept_and_resent"


@pytest.mark.parametrize("perfect_apd", [True, False])
def test_intercept_introduit_du_qber(perfect_apd):
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, perfect_apd=perfect_apd)

    assert r.alice_len() > 40
    assert not r.keys_match(), "l'attaque doit casser l'égalité des clés"
    assert 8 < r.n_errors()/r.alice_len()*100 < 42, "taux d'erreur attendu autour de 25 (± 12) %"


def test_eve_apprend_environ_trois_quarts_de_la_cle():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1)

    assert r.eve_knowledge() is not None
    assert 63 < r.eve_knowledge() < 87, "connaissance d'Eve attendue autour de 75 (± 12) %"


def test_intercept_reste_detectable_avec_peu_de_photons():
    """Même avec moins de photon, l'attaque reste détectable"""
    r = run_qkd(attack=ATTACK, average_emitted_photon=0.5, message_size=500)

    assert not r.keys_match()
    assert r.n_errors()/r.alice_len()*100 > 11

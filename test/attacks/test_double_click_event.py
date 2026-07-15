"""L'attaque par exploitation du double click event repose sur un principe simple.
    Dans l'éventualité ou Bob recoit plusieurs photons il a plusieurs possibilités
    - Dans le doute jeter les photons et noté la réception comme perdu
    - Choisir aléatoirement un photon
    Dans l'attaque c'est ce premier cas qui va nous intéresser. Lors de l'intercept and resent, Eve va renvoyer un grand nombre de photons. Si la base choisit
    par eve est la même que celle de bob, le photon sera correctement lu par un seul APD -> Pas de problème
    Dans le cas ou la bse n'est pas la même (et donc normalemnet une augmentation du QBER), les différents photons vont actionner les deux APDs de réception,
    ainsi si Bob décide de jeter les photons, le qubit sera considérer comme perdu, et le qber n'augmentera pas.

    QBER Estimé : 0%
    Clé Estimé : 100%
    Détectable : Non

    Args:
        Intercept (_type_): Héritage de factory.py dans intercept
"""    

import pytest
from manager_test import run_qkd

ATTACK = "DoubleClickEvent"

def test_eve_connait_quasiment_toute_la_cle_sans_detection():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, many_clicks_gestion="THROWS")

    assert r.n_errors() <= 1
    assert r.qber <= 1

def test_detecte_si_ne_jete_pas_les_photons():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, many_clicks_gestion="RANDOM")

    assert r.qber > 11

"""
Tests sans attaque (c'est tout)

pour lancer :  pytest test/attacks/test_without_attacks.py -v
"""

import pytest
from manager_test import run_qkd

# Nb de bits d'écart qu'on tolère à cause du bruit de timing de la simulation.


def test_canal_parfait_donne_cle_identique():
    """Canal parfait aucune erreur ne devrait surgir
    """
    r = run_qkd(attack=None, bit_flip=0, bit_loss=0, perfect_apd=True, average_emitted_photon=-1)

    assert r.alice_len() > 50, "la clé ne devrait pas être (presque) vide"
    assert r.n_errors() == 0#, "sans attaque ni bruit : il doit y avoir aucune erreur"


def test_bruit_bitflip_cree_des_erreurs():
    """Avec du bit-flip sur le canal (10 %), des erreurs apparaissent.
    """
    r = run_qkd(attack=None, perfect_apd=True, average_emitted_photon=-1, bit_flip=10)

    assert not r.keys_match()
    assert r.n_errors() > 3, "le bit-flip doit introduire des erreurs visibles"


def test_perte_raccourcit_la_cle_sans_erreur():
    """Avec de la perte sur le canal (40 %), la clé raccourcit mais reste correcte.

    Un photon perdu n'arrive jamais : le créneau est simplement ignoré. Les bits
    qui, eux, arrivent restent corrects -> pas d'erreur, juste une clé plus courte.
    """
    ideal = run_qkd(attack=None, perfect_apd=True, average_emitted_photon=-1)
    lossy = run_qkd(attack=None, perfect_apd=True, average_emitted_photon=-1, bit_loss=40)

    assert lossy.n_errors() == 0, "la perte ne doit pas créer d'erreur"
    assert lossy.alice_len() < ideal.alice_len(), "la perte doit raccourcir la clé"


def test_apd_reel_perd_des_photons_sans_erreur():
    """Apd réaliste, ainsi plus d'erreur"""
    ideal = run_qkd(attack=None, perfect_apd=True, average_emitted_photon=-1)
    lossy = run_qkd(attack=None, perfect_apd=False, average_emitted_photon=-1)

    assert lossy.alice_len() > 20
    assert lossy.n_errors() == 0
    assert lossy.alice_len() < ideal.alice_len(), "la perte doit raccourcir la clé"


@pytest.mark.parametrize("moyenne", [0.3, 1.0, 2.0])
def test_source_poisson_reste_sans_erreur(moyenne):
    """Avec une vrai source d'émission suivant une loi de poisson la clé reste exact masi raccourci
    """
    r = run_qkd(attack=None, average_emitted_photon=moyenne, perfect_apd=True)

    assert r.n_errors() == 0#, "l'incertitude d el'émission de doit pas introduire d'erreur"


def test_moins_de_photons_donne_une_cle_plus_courte():
    """Moins la source émet de photons en moyenne, plus la clé est courte.

    Avec une moyenne de 0.3 photon, beaucoup de ticks sont "vides" ; avec 1.0
    la source émet bien plus souvent au moins un photon.
    """
    peu = run_qkd(attack=None, average_emitted_photon=0.3, perfect_apd=True)
    plus = run_qkd(attack=None, average_emitted_photon=1.0, perfect_apd=True)

    assert peu.alice_len() < plus.alice_len()

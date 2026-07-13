"""
    L'attaque PNS repose sur le principe suivant :
    L'emetteur émet plus d'un photon en moyenne,
    Lorsque un seul photon est émis, eve le détruit,
    Lorsque plus d'un photon est émis, eve en garde un pour elle et laisse passer le(s) autre(s) tel quel
    Eve n'a plus qu'à attendre l'étape de sifting pour lire le photon dans la bonne base.

    QBER Estimé : 0%
    Clé Estimé : dépend du nombre de photons émis
    Détectable : Non
"""

import pytest
from manager_test import run_qkd

ATTACK = "PNS"


@pytest.mark.parametrize("moyenne", [0.5, 1.0, 2.0])
def test_pns_est_indetectable(moyenne):
    """PNS n'introduit aucune erreur : Alice et Bob gardent la même clé.
    """
    r = run_qkd(attack=ATTACK, average_emitted_photon=moyenne)

    assert r.alice_len() > 0, "la clé ne doit pas être vide"
    assert r.n_errors() == 0, "PNS ne doit pas créer d'erreur chez Bob"


@pytest.mark.parametrize("moyenne", [0.5, 1.0, 2.0])
def test_pns_eve_connait_toute_la_cle(moyenne):
    """Eve est censé connaitre toute la clé
    """
    r = run_qkd(attack=ATTACK, average_emitted_photon=moyenne)

    assert r.eve_knowledge() is not None
    assert r.eve_knowledge() == 100


def test_pns_plus_de_photons_donne_plus_de_cle():
    """Plus i y a de photon plus eve est forte
    """
    peu = run_qkd(attack=ATTACK, average_emitted_photon=0.5)
    plus = run_qkd(attack=ATTACK, average_emitted_photon=2.0)

    assert plus.alice_len() > peu.alice_len()


def test_pns_impossible_sur_source_ideale():
    """Avec un photon émis a chaque fois, eve ne connait pas la clé, cela lève une exception dans el code
    """
    with pytest.raises(Exception):
        run_qkd(attack=ATTACK, average_emitted_photon=-1)


def test_pns_avec_du_bruit_en_plus():
    """Le fait d'ajouter du bruit augmente le qber, amsi ce n'est pas l'attaque qui fait ca !
    """
    r = run_qkd(attack=ATTACK, average_emitted_photon=1.0, bit_flip=15)

    assert r.n_errors()/r.alice_len()*100 > 3, "le bruit du canal doit créer des erreurs chez Bob"
    assert r.eve_knowledge() is not None
    assert r.eve_knowledge() > 70, "malgré le bruit, Eve connaît l'essentiel de la clé"

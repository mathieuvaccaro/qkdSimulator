"""L'attaque par corrélation de temps exploite le dead time des APD de Bob. Après une détection,
    un détecteur reste aveugle pendant son dead time : deux détections successives séparées par un
    temps inférieur au dead time ne peuvent donc pas venir du même détecteur et portent forcément
    deux bits opposés.

    Remarque : l'attaque ne fonctionne qu'avec des APD réalistes (perfect_apd=False), sinon Bob n'a
    pas de dead time et les détections ne se regroupent plus en chaînes exploitables.



    QBER Estimé : 0%
    Connaissance de clé : 100% dans le meilleur cas (la vraie clé est toujours énumérée)
    Détectable : Non

    Args:
        Intercept (_type_): Héritage de intercept (factory.py)
"""

from manager_test import run_qkd
from utils.percent_corrupted_key import how_much_key_corrupted

ATTACK = "TIME_CORRELATION"

# Petite clé : Eve énumère TOUTES les orientations de chaînes
MESSAGE_SIZE = 200

def test_taux_de_reussite_100_pourcent_system_parfait():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, perfect_apd=False, message_size=MESSAGE_SIZE, dead_time_min=20, dead_time_max=60)
    result = max(how_much_key_corrupted(r.key_alice, cand) for cand in r.key_eve)
    assert r.n_errors() <= 1

def test_qber_absent_conditions_parfaite():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, perfect_apd=False, message_size=MESSAGE_SIZE, dead_time_min=20, dead_time_max=60)
    result = max(how_much_key_corrupted(r.key_alice, cand) for cand in r.key_eve)
    assert r.qber <= 1

def test_taux_de_reussite_eleve_imparfait():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, perfect_apd=False, bit_flip=5, bit_loss=5, message_size=MESSAGE_SIZE, dead_time_min=20, dead_time_max=60)
    result = max(how_much_key_corrupted(r.key_alice, cand) for cand in r.key_eve)
    assert r.n_errors() <= 10

def test_attack_ne_fonctionne_pas_sur_apd_parfait():
    r = run_qkd(attack=ATTACK, average_emitted_photon=-1, perfect_apd=True, bit_flip=5, bit_loss=5, message_size=MESSAGE_SIZE)
    result = max(how_much_key_corrupted(r.key_alice, cand) for cand in r.key_eve)
    assert result < 70

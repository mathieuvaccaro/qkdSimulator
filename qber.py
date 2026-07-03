import utils
import settings
from random import sample as rng_s


# For now, we simplify qber section (by centralization)
def qber_calculus(bits_alice, bits_bob):
    nb_qber = int(settings.qber_percent / 100 * len(bits_alice))
    if nb_qber == 0:  # pas assez de bits pour estimer le QBER
        return (0.0, remove_revealed_bits(bits_alice, []))
    random_indexes = rng_s(range(0, len(bits_alice)), nb_qber)
    qber_score = 0
    for idx in random_indexes:
        if bits_alice[idx] != bits_bob[idx]:  # on incrémente si les bits diffèrent
            qber_score += 1

    # QBER = erreurs / nombre de bits effectivement comparés (l'échantillon)
    return (qber_score / nb_qber * 100, remove_revealed_bits(bits_alice, random_indexes))


def remove_revealed_bits(key: list, indexes) -> list:
    return key # Pour l'insant on retourne la key tel quel, mais l'échange est public donc eve peut savoir quelle index retirer
    to_remove = set(indexes)
    return [bit for i, bit in enumerate(key) if i not in to_remove]
import settings
from random import sample as rng_s


"""Le calcul du qber fonctionne de la manière suivante :
On récupére tous les bits retenus après le sifting, on en tire au sort un certain nombre (qber_percent %) et on regarde la portion dont les bits diverge
Si cette valeur dépasse (qber_tolerance %) alors la communication est aborté."""

# For now, we simplify qber section (by centralization)
def qber_calculus(bits_alice : list[int], bits_bob : list[int]) -> float:
    """Estime le QBER en comparant un échantillon aléatoire (qber_percent %) des bits siftés d'Alice et Bob

    Args:
        bits_alice (list[int]): clé siftée d'Alice
        bits_bob (list[int]): clé siftée de Bob

    Returns:
        tuple[float, list]: (QBER en %, clé restante une fois les bits révélés retirés)
    """
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


def remove_revealed_bits(key: list[int], indexes : int) -> list:
    """Retire de la clé les bits révélés publiquement lors du calcul du QBER

    Args:
        key (list[int]): clé siftée
        indexes (int): indices des bits révélés à retirer

    Returns:
        list: clé sans les bits révélés
    """
    return key # Pour l'insant on retourne la key tel quel, mais l'échange est public donc eve peut savoir quelle index retirer
    to_remove = set(indexes)
    return [bit for i, bit in enumerate(key) if i not in to_remove]
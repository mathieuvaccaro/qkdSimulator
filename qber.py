import utils
import settings
from random import sample as rng_s


# For now, we simplify qber section (by centralization)
def qber_calculus(bits_alice, bits_bob):
    nb_qber = int(settings.qber_percent / 100 * len(bits_alice))
    print(nb_qber)
    random_indexes = rng_s(range(0, len(bits_alice)), nb_qber)
    qber_score = 0
    for idx in random_indexes:
        if bits_alice[idx] != bits_bob[idx]:  # on incrémente si les bits diffèrent
            qber_score += 1
    
    return qber_score
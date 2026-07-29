import components.receiver as receiver
import components.sender as sender
from random import randint as rng
from utils.colors import bcolors
import settings

"""L'intérêt du sifting est le suivante :
Alice et Bob échangent leurs bases publiquement et garde seulement les bits ayant été encodé et lu avec la même base
"""

def sifting(self, other_bases : list[int]) -> list[int]:
    """Effectue le sifting : ne conserve que les bits dont la base d'encodage/lecture est identique de part et d'autre

    Args:
        other_bases (list[int]): bases choisies par l'autre partie (Alice ou Bob)

    Returns:
        list[int]: clé siftée (bits gardés dans l'ordre)
    """
    key = []
    if(len(other_bases) != len(self.chosen_bases)):
        raise Exception(f"Basis aren't same length ! communication abortin {len(self.chosen_bases)} / {len(other_bases)}....")
    
    # Dans l'éventualité, ou la base n'a pas assez de bit, c'est srement parce que le(s) premier(s) bits ne sont pas arrivé
    for i in range(len(self.chosen_bases)):
        if(other_bases[i] == self.chosen_bases[i]):
            if(isinstance(self, receiver.Receiver)):
                key.append(self.measured_bits[i])
            else:
                key.append(self.sent_bits[i])
    return key
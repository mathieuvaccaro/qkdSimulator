import components.receiver as receiver
import components.sender as sender
from random import randint as rng
from utils.colors import bcolors

"""L'intérêt du sifting est le suivante :
Alice et Bob échangent leurs bases publiquement et garde seulement les bits ayant été encodé et lu avec la même base
"""

def sifting(self, other_bases : list[int]) -> list[int]:
    key = []
    if(len(other_bases) != len(self.chosen_bases)):
        raise Exception(f"Basis aren't same length ! communication abortin {len(self.chosen_bases)} / {len(other_bases)}")
    
    for i in range(len(self.chosen_bases)):
        if(other_bases[i] == self.chosen_bases[i]):
            if(isinstance(self, receiver.Receiver)):
                key.append(self.measured_bits[i])
            else:
                key.append(self.sent_bits[i])
    return key


# We'll look bits which measured with same basis thann Alice AND Bob. If eve choose another basis than ALice and bob, bit will be selected randomly (car on a choisi une mauvaise base)
def eve_sifting(eve, alice_bases : list[int], bob_bases : list[int]) -> list[int]:
    if(len(eve.chosen_bases) != len(alice_bases)):
        raise Exception(f"Basis aren't same length ! communication abortin {len(eve.chosen_bases)} / {len(alice_bases)}")
    
    
    key = []
    for i in range(len(eve.chosen_bases)):
        if(alice_bases[i] == bob_bases[i]):
            key.append(eve.measured_bits[i])
    return key
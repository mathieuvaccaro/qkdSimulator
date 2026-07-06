import components.receiver as receiver
import components.sender as sender
from random import randint as rng

from utils.colors import bcolors

def sifting(self, other_bases : list[int]):
    key = []
    if(len(other_bases) != len(self.chosen_bases)):
        print(bcolors.WARNING + "Basis aren't same length ! communication aborting")
        return False
    
    for i in range(len(other_bases)):
        # Same basis used
        if(other_bases[i] == self.chosen_bases[i]):
            # Variable name change between sender and receiver
            if(isinstance(self, receiver.Receiver)):
                key.append(self.measured_bits[i])
            else:
                key.append(self.sent_bits[i])

    return key


# We'll look bits which measured with same basis thann Alice AND Bob. If eve choose another basis than ALice and bob, bit will be selected randomly (car on a choisi une mauvaise base)
def eve_sifting(eve, alice_bases : list[int], bob_bases : list[int]):
    key = []
    for i in range(len(eve.chosen_bases)):
        if(alice_bases[i] == bob_bases[i]):
            key.append(eve.measured_bits[i])
    return key
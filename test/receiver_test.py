import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # To import apd module :(

from apd import Apd
import receiver

sended_bit = rng(0, 1)
alice_basis = rng(0, 1)
sended_state = STATES[sended_bit, alice_basis]
alice_bases.append(alice_basis)
alice_bits.append(sended_bit)

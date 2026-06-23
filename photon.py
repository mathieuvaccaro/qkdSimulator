import itertools

# Comment représenter l'état quantique d'un photon

# Create photon :
# ID : just a unique id


class Photon(object):
    id = itertools.count() # Just to have a auto incremental id
    polarisation = 0 # Angle from 0 (counterclockwise)
    base = "" # Rectiligne, diagonal.

    def __init__(self, id, polarisation, base):
        self.id = id
        self.polarisation = polarisation
        self.base = base

def createPhoton(polarisation, base)
import qutip
import numpy as np

def get_states():
    # Rectilinear states
    H = qutip.basis(2, 0)  # Horizontal
    V = qutip.basis(2, 1)  # Vertical
    # Diagonal states (+45° and -45°)
    D = ((H + V) / np.sqrt(2)).unit()
    DM = ((H - V) / np.sqrt(2)).unit()
    STATES = {
        (0, 0): H,    # bit 0, rectilinear
        (1, 0): V,    # bit 1, rectilinear
        (0, 1): D,    # bit 0, diagonal
        (1, 1): DM,   # bit 1, diagonal
    }

    return STATES

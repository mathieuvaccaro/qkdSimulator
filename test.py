import qutip
import numpy as np
import matplotlib.pyplot as plt

N = 1000

measureHR = 0
measureHD = 0
measureVR = 0
measureVD = 0
measureDR = 0
measureDD = 0

# Créer un vecteur (qutip.basis(X, Y) avec X = dimension, Y = bit assoié):
H = qutip.basis(2, 0) # Horizontal
V = qutip.basis(2, 1) # Vertical

# Mise en état de superposition (45 et -45°)
D = ((H+V) / np.sqrt(2)).unit() 
DM = ((H-V) / np.sqrt(2)).unit()

for _ in range(N):
    # Mesure
    # ket2dm convertie le vecteur en matrice de densité.
    measureHR += qutip.measurement.measure(H, [qutip.ket2dm(H),  qutip.ket2dm(V)])[0]
    measureHD += qutip.measurement.measure(H, [qutip.ket2dm(D),  qutip.ket2dm(DM)])[0]
    measureVR += qutip.measurement.measure(V, [qutip.ket2dm(H),  qutip.ket2dm(V)])[0]
    measureVD += qutip.measurement.measure(V, [qutip.ket2dm(D),  qutip.ket2dm(DM)])[0]
    measureDR += qutip.measurement.measure(D, [qutip.ket2dm(H),  qutip.ket2dm(V)])[0]
    measureDD += qutip.measurement.measure(D, [qutip.ket2dm(D),  qutip.ket2dm(DM)])[0]  



# GRAPH PART MADE BY AI
labels = ["H\nRectiligne", "H\nDiagonale",
          "V\nRectiligne", "V\nDiagonale",
          "D\nRectiligne", "D\nDiagonale"]

# convertir les compteurs en pourcentage de '1'
probs = [m / N * 100 for m in
         [measureHR, measureHD, measureVR, measureVD, measureDR, measureDD]]

# vert = bonne base, orange = mauvaise base
couleurs = ["#2ecc71", "#e67e22",
            "#2ecc71", "#e67e22",
            "#e67e22", "#2ecc71"]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(labels, probs, color=couleurs, edgecolor="white", width=0.55)

# valeur au dessus de chaque barre
for bar, p in zip(bars, probs):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{p:.1f}%", ha="center", fontsize=11,
            fontweight="bold", color="#2c3e50")

ax.axhline(50, color="gray", linestyle="--", linewidth=1.2, label="50% (aléatoire)")
ax.set_ylim(0, 115)
ax.set_ylabel("Probabilité d'obtenir '1' (%)")
ax.set_title(f"Impact du choix de la base de mesure  —  N={N} tirages")

from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(color="#2ecc71", label="Bonne base  →  déterministe"),
    Patch(color="#e67e22", label="Mauvaise base  →  50/50"),
], loc="upper right")

ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("impact_base.png", dpi=150)
plt.show()
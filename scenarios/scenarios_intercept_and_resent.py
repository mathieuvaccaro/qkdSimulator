r"""Scénario : attaque INTERCEPT AND RESEND.

Eve se place entre Alice et Bob, mesure chaque qubit dans une base tirée au hasard, puis
réémet vers Bob l'état qu'elle a lu. Une fois sur deux elle se trompe de base et réémet
un état faux : Bob a alors une chance sur deux de lire l'inverse du bit d'Alice, d'où un
QBER d'environ 25 %.

Ce qu'il montre :
  - l'attaque est bruyante : le QBER dépasse largement la tolérance de 11 %, Alice et Bob
    détectent Eve et abandonnent la communication ;
  - le bruit du canal s'ajoute à celui d'Eve, il ne la masque pas ;
  - avec trop peu de qubits, l'estimation du QBER (faite sur 20 % des bits siftés) devient
    un tirage au sort : sur 60 qubits elle ne porte que sur 6 bits, et peut donc passer
    sous la tolérance et laisser Eve tranquille. Comparer, dans chaque liaison, le "QBER
    estimé" avec l'écart réel "Accord Alice/Bob" : l'écart entre les deux se resserre sur
    la clé longue. C'est l'argument pour échanger des clés longues.

Lancement : python3 scenarios/scenarios_intercept_and_resent.py
"""

import os
import sys

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from scenario_runner import run_scenario

TITRE = "SCENARIO — Intercept and Resend (mesure directe)"

DESCRIPTION = """
QBER attendu     : ~ 25 %
Connaissance Eve : ~ 75 % de la clé siftée
Détectable       : oui, c'est l'attaque la plus visible
"""

ATTAQUE = "INTERCEPT_AND_RESENT"

COMMUN = {"message_size": 300, "message_interval": 4, "perfect_apd": True}

VARIANTES = [
    ("Référence sans Eve", {"attack": None}),
    ("Eve intercepte tout", {}),
    ("Eve + canal bruité (3 % / 3 %)", {"bit_loss": 3.0, "bit_flip": 3.0}),
    ("Clé courte (60 qubits)", {"message_size": 60}),
    ("Clé longue (600 qubits)", {"message_size": 600}),
]

if __name__ == "__main__":
    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

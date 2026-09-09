r"""Scénario : attaque TROJAN HORSE (cheval de Troie optique).

Eve envoie un faisceau lumineux dans l'émetteur d'Alice ; par réflexion (loi de Fresnel)
une partie de la lumière lui revient en portant l'information de la base d'encodage. Eve
mesure donc chaque qubit dans LA BONNE base, lit le bon bit, et réémet un état rigoureusement
identique à celui d'Alice.

Ce qu'il montre :
  - Eve n'introduit aucune erreur : le QBER reste celui du canal, l'attaque est invisible ;
  - sa connaissance de la clé est totale (~100 %), c'est le pire cas possible ;
  - allonger la clé n'y change rien : contrairement à l'intercept and resend, il n'y a
    aucune statistique qui finit par trahir Eve. Seule une protection matérielle
    (isolateur optique côté Alice) est efficace.

Lancement : python3 scenarios/scenarios_trojan_horse.py
"""

import os
import sys

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from scenario_runner import run_scenario

TITRE = "SCENARIO — Trojan Horse (canal auxiliaire)"

DESCRIPTION = """
QBER attendu     : ~ 0 % (celui du canal uniquement)
Connaissance Eve : ~ 100 % de la clé siftée
Détectable       : non, il n'y a aucune trace dans les données échangées
"""

ATTAQUE = "TROJAN_HORSE"

COMMUN = {"message_size": 300, "message_interval": 4, "perfect_apd": True}

VARIANTES = [
    ("Référence sans Eve", {"attack": None}),
    ("Eve connaît la base d'Alice", {}),
    ("Eve + canal bruité (3 % flip)", {"bit_flip": 3.0}),
    ("Clé longue (600 qubits)", {"message_size": 600}),
]

if __name__ == "__main__":
    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

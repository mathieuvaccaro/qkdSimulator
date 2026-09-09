r"""Scénario de référence : AUCUNE attaque.

Avant d'accuser Eve, il faut savoir à quoi ressemble une liaison saine. Ce scénario ne
lance aucune attaque et fait uniquement varier le canal et les détecteurs de Bob.

Ce qu'il montre :
  - une liaison parfaite donne un QBER de 0 % et deux clés strictement identiques ;
  - le bruit du canal (bit flip) se retrouve directement dans le QBER : à 9 % de flip on
    frôle déjà la tolérance de 11 % alors qu'il n'y a personne sur la ligne (faux positif).
    Le QBER n'étant estimé que sur 20 % des bits siftés, sa valeur danse d'un run à
    l'autre autour de l'écart réel Alice/Bob affiché juste au dessus ;
  - les pertes et les apds réalistes (gate + dead time) ne créent pas d'erreur, ils
    réduisent le débit : moins de bits détectés, donc une clé siftée plus courte.

Lancement : python3 scenarios/scenarios_sans_attaque.py
"""

import os
import sys

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from scenario_runner import run_scenario

TITRE = "SCENARIO — Liaison de référence (aucune attaque)"

DESCRIPTION = """
QBER attendu     : celui du canal uniquement (~ bit_flip)
Connaissance Eve : aucune, elle n'est pas sur la ligne
Objectif         : mesurer le bruit "normal" pour ne pas le confondre avec une attaque
"""

ATTAQUE = None

# Paramètres communs à toutes les variantes
COMMUN = {"message_size": 300, "message_interval": 4, "perfect_apd": True}

# (nom de la variante, paramètres qui changent par rapport à COMMUN)
VARIANTES = [
    ("Canal et APD parfaits", {"bit_loss": 0.0, "bit_flip": 0.0}),
    ("Canal réaliste (2 % perte, 2 % flip)", {"bit_loss": 2.0, "bit_flip": 2.0}),
    ("Canal très bruité (5 % perte, 9 % flip)", {"bit_loss": 5.0, "bit_flip": 9.0}),
    ("APD réalistes (gate + dead time)", {"perfect_apd": False, "message_size": 150, "message_interval": 20,
                                          "gate_on_duration": 10, "gate_off_duration": 10,
                                          "dead_time_min": 20, "dead_time_max": 60}),
]

if __name__ == "__main__":
    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

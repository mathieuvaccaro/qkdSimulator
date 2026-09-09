r"""Scénario : attaque PNS (Photon Number Splitting).

La source d'Alice n'est pas parfaite : le nombre de photons émis par qubit suit une loi de
Poisson de moyenne µ (average_emitted_photon). Eve en profite :
  - impulsion à 1 photon  -> elle le garde et ne transmet rien (Bob ne verra rien) ;
  - impulsion à 2 photons -> elle en garde un et laisse passer l'autre, intact.
Elle attend ensuite que les bases soient publiques pour mesurer ses photons dans la bonne
base : elle lit le bit sans jamais avoir introduit la moindre erreur.

Ce qu'il montre :
  - le QBER reste à 0 : l'attaque est INDÉTECTABLE par le QBER seul, c'est le taux de
    détection de Bob qui s'effondre et qui doit mettre la puce à l'oreille ;
  - plus la source est bavarde (µ grand), plus Bob reçoit de bits... et plus Eve en sait ;
  - une source faible (µ petit) ne protège pas la clé (Eve connaît toujours tout ce que
    Bob reçoit), elle écroule seulement le débit, car Eve bloque toutes les impulsions à
    un seul photon.

Remarque : la liaison de référence utilise une source idéale (µ = -1, exactement un photon).
Avec une source de Poisson et sans Eve, plusieurs photons du même slot arrivent jusqu'à Bob
et déclenchent ses deux apds ; le simulateur jette alors le bit, ce qui gonfle artificiellement
le QBER de la référence. Eve, elle, ne laisse jamais passer plus d'un photon à la fois.

Lancement : python3 scenarios/scenarios_pns.py
"""

import os
import sys

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from scenario_runner import run_scenario

TITRE = "SCENARIO — Photon Number Splitting (faille de la source)"

DESCRIPTION = """
QBER attendu     : ~ 0 %, Eve ne réémet jamais d'état faux
Connaissance Eve : dépend de µ (moyenne de photons par impulsion)
Détectable       : non par le QBER, seulement par le taux de détection de Bob
Attention        : l'attaque exige une source imparfaite (average_emitted_photon != -1)
"""

ATTAQUE = "PNS"

COMMUN = {"message_size": 400, "message_interval": 4, "perfect_apd": True,
          "average_emitted_photon": 1.0}

VARIANTES = [
    ("Référence sans Eve (source idéale)", {"attack": None, "average_emitted_photon": -1}),
    ("Source faible (µ = 0.5)", {"average_emitted_photon": 0.5}),
    ("Source standard (µ = 1.0)", {}),
    ("Source bavarde (µ = 2.0)", {"average_emitted_photon": 2.0}),
    ("Source très bavarde (µ = 3.0)", {"average_emitted_photon": 3.0}),
]

if __name__ == "__main__":
    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

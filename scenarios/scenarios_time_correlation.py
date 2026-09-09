r"""Scénario : attaque par CORRELATION DE TEMPS (dead time des apds).

Après chaque détection, un apd est aveugle pendant son dead time. Si ce dead time est
grand devant la période d'émission, deux détections très rapprochées ne peuvent pas venir
du même apd : elles portent donc forcément des bits OPPOSÉS. Eve, qui se contente
d'horodater les qubits sans les mesurer (elle est totalement passive), reconstruit des
chaînes de bits relatifs, puis énumère les 2^C orientations possibles des C chaînes.

Ce qu'il montre :
  - l'attaque est passive : QBER inchangé, aucune trace, indétectable ;
  - elle ne rapporte quelque chose QUE si le dead time est long devant l'intervalle
    d'émission : avec un dead time court, aucune chaîne ne se forme et Eve ne fait pas
    mieux que le hasard ;
  - le résultat n'est pas une clé mais une LISTE de clés candidates : print_results.py
    affiche la meilleure d'entre elles (le pire cas pour Alice et Bob). Le vrai indicateur
    est donc le NOMBRE de candidates : la bonne clé est presque toujours dans le lot, tout
    l'enjeu pour Eve est que le lot soit petit. Dead time long = peu de candidates = danger.

Attention : l'énumération est exponentielle (2^C). On garde donc peu de qubits et un
budget de temps court (timing_attack, en secondes) : au-delà, Eve rend ce qu'elle a.

Lancement : python3 scenarios/scenarios_time_correlation.py
"""

import os
import sys

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from scenario_runner import run_scenario

TITRE = "SCENARIO — Time Correlation (dead time des apds)"

DESCRIPTION = """
QBER attendu     : inchangé, Eve ne touche jamais aux qubits
Connaissance Eve : jusqu'à 100 % dans le meilleur cas, mais parmi 2^C candidates
Détectable       : non, l'attaque est entièrement passive
Attention        : énumération exponentielle, d'où la clé courte et timing_attack
"""

ATTAQUE = "TIME_CORRELATION"

# Les apds de Bob doivent être réalistes : c'est leur dead time qui fuit l'information
COMMUN = {"message_size": 80, "message_interval": 20, "perfect_apd": False,
          "gate_on_duration": 20, "gate_off_duration": 0, "timing_attack": 3}

VARIANTES = [
    ("Référence sans Eve", {"attack": None, "dead_time_min": 40, "dead_time_max": 80}),
    ("Dead time court (2-6 ms)", {"dead_time_min": 2, "dead_time_max": 6}),
    ("Dead time long (40-80 ms)", {"dead_time_min": 40, "dead_time_max": 80}),
    ("Dead time très long (60-120 ms)", {"dead_time_min": 60, "dead_time_max": 120}),
]

if __name__ == "__main__":
    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

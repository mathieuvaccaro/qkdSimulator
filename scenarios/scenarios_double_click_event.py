r"""Scénario : attaque par DOUBLE CLICK EVENT.

C'est un intercept and resend amélioré : au lieu de réémettre un seul photon, Eve en
réémet une rafale (emission_click_event). Quand elle a choisi la même base que Bob, tous
les photons vont sur le même apd : une détection propre. Quand elle s'est trompée de base,
les photons se répartissent sur les DEUX apds de Bob : c'est un double click.

Tout se joue alors sur la façon dont Bob traite ce double click (many_clicks_gestion) :
  - "THROWS" : il jette le slot et le compte comme perdu. Les cas où Eve s'est trompée
    disparaissent des statistiques, le QBER retombe à ~0 et l'attaque devient invisible ;
  - "RANDOM" : il garde un des deux bits au hasard. Les erreurs restent, le QBER remonte
    et Eve se fait détecter comme dans un intercept and resend classique.

Ce qu'il montre : une décision d'implémentation côté détecteur, qui semble prudente
("dans le doute, je jette"), suffit à ouvrir une faille critique. La signature de l'attaque
n'est donc plus dans le QBER mais dans le taux de slots perdus, qui explose (~50 %).
Une rafale trop petite (2 photons) ne déclenche pas toujours le double click : des erreurs
subsistent et Eve se fait repérer.

Le dead time des apds de Bob fait partie du montage : c'est lui qui limite chaque apd à un
seul click par slot. Avec des apds parfaits, les photons de la rafale cliquent tous et Bob
finit par jeter la totalité de la clé, attaque ou pas.

Lancement : python3 scenarios/scenarios_double_click_event.py
"""

import os
import sys

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from scenario_runner import run_scenario

TITRE = "SCENARIO — Double Click Event (faille du détecteur)"

DESCRIPTION = """
QBER attendu     : ~ 0 % si Bob jette les doubles clicks, ~ 25 % s'il tire au sort
Connaissance Eve : élevée dans les deux cas (elle a mesuré tous les qubits)
Détectable       : uniquement si Bob surveille son taux de doubles clicks
"""

ATTAQUE = "DOUBLE_CLICK_EVENT"

# Les apds de Bob doivent être réalistes : c'est leur dead time (ici 2-3 ms pour une clock
# à 4 ms) qui limite chaque apd à UN seul click par slot, puis le laisse récupérer avant le
# slot suivant. Sans lui, les 10 photons d'Eve cliquent tous et Bob jette absolument tout.
COMMUN = {"message_size": 200, "message_interval": 4, "perfect_apd": False,
          "gate_on_duration": 4, "gate_off_duration": 0, "dead_time_min": 2, "dead_time_max": 3,
          "emission_click_event": 10, "many_clicks_gestion": "THROWS"}

VARIANTES = [
    ("Référence sans Eve", {"attack": None}),
    ("Bob jette les doubles clicks", {"many_clicks_gestion": "THROWS"}),
    ("Bob tire un bit au hasard", {"many_clicks_gestion": "RANDOM"}),
    ("Eve discrète : 2 photons", {"emission_click_event": 2}),
    ("Eve bruyante : 20 photons", {"emission_click_event": 20}),
]

if __name__ == "__main__":
    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

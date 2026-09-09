r"""
   _____                          _       
  / ____|                        (_)      
 | (___   ___ ___ _ __   __ _ _ __ _  ___  ___
  \___ \ / __/ _ \ '_ \ / _` | '__| |/ _ \/ __|
  ____) | (_|  __/ | | | (_| | |  | | (_) \__ \
 |_____/ \___\___|_| |_|\__,_|_|  |_|\___/|___/

Moteur commun à tous les scénarios du dossier scenarios/.

Un scénario, c'est UNE attaque jouée plusieurs fois avec des paramètres différents
(les "variantes"), puis affichée par print_results.py. Tout passe par run_qkd
(manager_scenario.py) : l'intérêt est justement de ne JAMAIS avoir à éditer settings.py
à la main pour lancer un cas de figure.

Un fichier de scénario se résume donc à :

    ATTAQUE   = "INTERCEPT_AND_RESENT"
    COMMUN    = {"message_size": 300, "message_interval": 4}
    VARIANTES = [("Référence sans Eve", {"attack": None}),
                 ("Canal bruité",       {"bit_flip": 3})]

    run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)

Les paramètres de COMMUN s'appliquent à toutes les variantes, ceux d'une variante
écrasent COMMUN. La clé spéciale "attack" permet à une variante de changer d'attaque
(ou de la couper avec None) pour servir de point de comparaison.
"""

import os
import sys
import time

# Racine du projet + dossier scenarios/ : permet de lancer le fichier depuis n'importe où
_ICI = os.path.dirname(os.path.abspath(__file__))
for _chemin in (os.path.dirname(_ICI), _ICI):
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

from manager_scenario import run_qkd
from print_results import LARGEUR, print_result
from utils.colors import bcolors


def _liberer_threads(res):
    """Arrête les clocks encore vivantes une fois la communication terminée.

    Chaque apd démarre sa propre clock dans un thread (cf. components/apd.py) et personne
    ne l'arrête à la fin de l'échange. Sans ce nettoyage, les threads des variantes déjà
    jouées continuent de ticker pendant les suivantes, et le script ne rend jamais la main
    à la fin (les threads ne sont pas des daemons). On ne touche à rien tant que la
    liaison n'est pas finie : à ce stade les clés sont déjà calculées.

    Args:
        res: QkdResult de la liaison qui vient d'être jouée
    """
    entites = [res.bob, res.eve]
    clocks = [getattr(res.bob, "clk", None)]  # la clock commune Alice/Bob

    for entite in entites:
        if entite is None:
            continue
        for nom_apd in ("apd0", "apd1"):
            apd = getattr(entite, nom_apd, None)
            clocks.append(getattr(apd, "clk", None))

    for clk in clocks:
        if clk is not None:
            clk.stop()


def _entete(titre : str, description : str, attaque, commun : dict, nb_variantes : int):
    """Affiche l'en-tête du scénario : ce qu'on teste et dans quelles conditions communes

    Args:
        titre (str): titre du scénario
        description (str): explication de l'attaque (plusieurs lignes possibles)
        attaque: flag de l'attaque jouée (None si aucune)
        commun (dict): paramètres appliqués à toutes les variantes
        nb_variantes (int): nombre de liaisons qui vont être jouées
    """
    print()
    print(bcolors.BOLD + bcolors.HEADER + "  ╔" + "═" * LARGEUR + "╗")
    print(f"  ║ {titre:<{LARGEUR - 2}} ║")
    print("  ╚" + "═" * LARGEUR + "╝" + bcolors.ENDC)

    for ligne in description.strip().splitlines():
        print(f"  {ligne.strip()}")

    print()
    print(f"  Attaque         : {attaque if attaque is not None else 'aucune'}")
    if commun:
        morceaux = []
        for nom, valeur in commun.items():
            morceaux.append(f"{nom}={valeur}")
        print(f"  Communs         : {', '.join(morceaux)}")
    print(f"  Variantes       : {nb_variantes}")
    print()


def run_scenario(titre : str, description : str, attaque, variantes : list, commun : dict = None):
    """Joue toutes les variantes d'un scénario puis affiche le résultat complet

    Args:
        titre (str): titre du scénario
        description (str): explication de l'attaque et de ce que le scénario cherche à montrer
        attaque: flag de l'attaque (cf. attacks/attack_manager.py), None pour aucune
        variantes (list): liste de couples (nom de la variante, paramètres pour run_qkd)
        commun (dict, optional): paramètres communs à toutes les variantes. Defaults to None.

    Returns:
        list: les QkdResult joués, dans l'ordre des variantes
    """
    _entete(titre, description, attaque, commun or {}, len(variantes))

    results = []
    etiquettes = []
    depart = time.time()

    for numero, (nom, params) in enumerate(variantes, start=1):
        # Les paramètres de la variante écrasent ceux du scénario
        reglages = dict(commun or {})
        reglages.update(params)

        # Une variante peut couper l'attaque (attack=None) pour servir de référence
        attaque_variante = reglages.pop("attack", attaque)

        print(f"  [{numero}/{len(variantes)}] {nom} ...", end="", flush=True)
        chrono = time.time()

        try:
            resultat = run_qkd(attack=attaque_variante, **reglages)
        except Exception as erreur:
            # Une variante mal configurée ne doit pas faire tomber tout le scénario
            print(bcolors.FAIL + f" échec : {erreur}" + bcolors.ENDC)
            continue

        _liberer_threads(resultat)
        results.append(resultat)

        etiquettes.append((nom, params))
        print(f" ok ({time.time() - chrono:.1f}s)")

    print(f"\n  Scénario joué en {time.time() - depart:.1f}s")
    print_result(results, etiquettes)
    return results

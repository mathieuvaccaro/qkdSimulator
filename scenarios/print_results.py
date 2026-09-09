r"""Affichage des résultats d'un scénario.

Un scénario est une suite de communications QKD. Chaque "liaison" est un QkdResult
renvoyé par manager.run_communication() (ou scenarios/manager_scenario.py).

Ce fichier ne fait QUE de l'affichage : aucune mesure n'est refaite ici, tout est relu
depuis les objets contenus dans le résultat (alice, bob, eve, les clés et le qber).

Remarque : les paramètres de settings.py sont globaux et sont écrasés à chaque run
(cf. manager_scenario.run_qkd). On ne peut donc pas leur faire confiance après coup pour
décrire une liaison en particulier : les spécificités de chaque échange sont relues sur
les objets eux-mêmes (alice.message_size, les apds de bob, la classe d'Eve...).
Seuls les paramètres réellement communs à tout le scénario (protocole, tolérance du
qber) sont pris dans settings.py.
"""

import os
import sys

# Racine du projet = .../qkdSimulator (on remonte de scenarios/), sinon "import manager" échoue
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import settings
from manager import QkdResult
from utils.colors import bcolors

LARGEUR = 84        # Largeur des encadrés
APERCU_BITS = 48    # Nombre de bits affichés dans un aperçu de clé
HASARD = 50.0       # Ce qu'Eve obtient en devinant au hasard (1 bit sur 2), en %

# Noms lisibles des attaques, la clé est le nom de la classe (cf. attacks/attack_manager.py)
NOMS_ATTAQUES = {
    "InterceptAndResent": ("Intercept & Resend", "Mesure directe / individuelle"),
    "Pns": ("Photon Number Splitting", "Source / multi-photon"),
    "TrojanHorse": ("Trojan Horse", "Canal auxiliaire (side-channel)"),
    "DoubleClickEvent": ("Double Click Event", "Detecteur / double click"),
    "CorrelationTime": ("Time Correlation", "Detecteur / dead time (stat.)"),
}


r"""
  _    _ _   _ _ _ _        _           
 | |  | | | (_) (_) |      (_)          
 | |  | | |_ _| |_| |_ __ _ _ _ __ ___  
 | |  | | __| | | | __/ _` | | '__/ _ \ 
 | |__| | |_| | | | || (_| | | | |  __/ 
  \____/ \__|_|_|_|\__\__,_|_|_|  \___| 
"""


def _nom_attaque(eve) -> tuple:
    """Retrouve le nom lisible de l'attaque à partir de l'objet d'Eve

    Args:
        eve: intercepteur de la liaison (None si aucune attaque)

    Returns:
        tuple: (nom de l'attaque, catégorie)
    """
    if eve is None:
        return ("Aucune", "Canal libre (Eve est absente)")
    nom_classe = type(eve).__name__
    return NOMS_ATTAQUES.get(nom_classe, (nom_classe, "Attaque non répertoriée"))


def _est_statistique(key_eve) -> bool:
    """Dit si la "clé" d'Eve est en réalité une liste de clés candidates.

    C'est le cas de l'attaque par corrélation de temps qui, étant statistique, renvoie
    toutes les clés possibles au lieu d'une seule (cf. attacks/correlations_time.py).

    Args:
        key_eve: clé (ou liste de clés) reconstruite par Eve

    Returns:
        bool: True si key_eve est une liste de clés candidates
    """
    return isinstance(key_eve, list) and len(key_eve) > 0 and isinstance(key_eve[0], list)


def _ressemblance(keyA : list[int], keyB : list[int]):
    """Pourcentage de bits identiques entre deux clés, calculé sur la partie commune.

    Contrairement à utils/percent_corrupted_key.py, cette version ne râle pas quand les
    tailles diffèrent (l'écart de taille est affiché à part) et renvoie None si la
    comparaison n'a aucun sens.

    Args:
        keyA (list[int]): clé 1
        keyB (list[int]): clé 2

    Returns:
        float | None: pourcentage de bits identiques, None si incomparable
    """
    if not keyA or not keyB:
        return None

    taille = min(len(keyA), len(keyB))
    identiques = 0
    for i in range(taille):
        if keyA[i] == keyB[i]:
            identiques += 1
    return identiques / taille * 100


def _erreurs(keyA : list[int], keyB : list[int]) -> int:
    """Nombre de bits qui diffèrent entre deux clés (sur la partie commune)

    Args:
        keyA (list[int]): clé 1
        keyB (list[int]): clé 2

    Returns:
        int: nombre de bits différents
    """
    compteur = 0
    for i in range(min(len(keyA), len(keyB))):
        if keyA[i] != keyB[i]:
            compteur += 1
    return compteur


def _connaissance_eve(res : QkdResult) -> tuple:
    """Part de la clé d'Alice réellement connue par Eve.

    Dans le cas d'une attaque statistique (liste de candidates), on retient la meilleure
    candidate : c'est le pire cas pour Alice et Bob.

    Args:
        res (QkdResult): résultat de la liaison

    Returns:
        tuple: (pourcentage | None, nombre de candidates, meilleure clé d'Eve | None)
    """
    if res.eve is None or res.key_eve is None:
        return (None, 0, None)

    if _est_statistique(res.key_eve):
        meilleur_score = None
        meilleure_cle = None
        for candidate in res.key_eve:
            score = _ressemblance(res.key_alice, candidate)
            if score is not None and (meilleur_score is None or score > meilleur_score):
                meilleur_score = score
                meilleure_cle = candidate
        return (meilleur_score, len(res.key_eve), meilleure_cle)

    return (_ressemblance(res.key_alice, res.key_eve), 1, res.key_eve)


def _verdict(qber : float, eve_pct, attaquee : bool) -> tuple:
    """Donne un verdict de sécurité à la liaison (même logique que benchmark.py)

    Args:
        qber (float): qber estimé, en %
        eve_pct (float | None): part de la clé connue par Eve, en % (None sans attaque)
        attaquee (bool): True si une attaque est active sur la liaison

    Returns:
        tuple: (verdict, couleur)
    """
    # Pas d'Eve sur le canal : il ne reste que le bruit du canal et des apds
    if not attaquee:
        if qber > settings.qber_tolerance:
            return ("CANAL BRUITE", bcolors.WARNING)
        return ("SAINE", bcolors.OKGREEN)

    if qber > settings.qber_tolerance:
        return ("DETECTEE", bcolors.OKCYAN)          # Alice et Bob abandonnent la communication
    if eve_pct is not None and eve_pct >= 90:
        return ("CRITIQUE", bcolors.FAIL)            # Invisible ET Eve a (presque) toute la clé
    if qber >= settings.qber_tolerance / 2:
        return ("SUSPECTE", bcolors.WARNING)         # Sous la tolérance mais anormalement haut
    return ("INOFFENSIVE", bcolors.OKGREEN)          # Eve n'en sait pas plus que le hasard


r"""
  ______                    _   _                      
 |  ____|                  | | | |                     
 | |__ ___  _ __ _ __ ___   __ _| |_| |_ __ _  __ _  ___ 
 |  __/ _ \| '__| '_ ` _ \ / _` | __| __/ _` |/ _` |/ _ \
 | | | (_) | |  | | | | | | (_| | |_| || (_| | (_| |  __/
 |_|  \___/|_|  |_| |_| |_|\__,_|\__|\__\__,_|\__, |\___|
                                               __/ |     
                                              |___/      
"""


def _pourcent(valeur, suffixe=" %") -> str:
    """Met en forme un pourcentage (ou "n/a" si la valeur n'existe pas)

    Args:
        valeur (float | None): valeur à afficher
        suffixe (str, optional): unité collée à la valeur. Defaults to " %".

    Returns:
        str: la valeur formatée
    """
    if valeur is None:
        return "n/a"
    return f"{valeur:.2f}{suffixe}"


def _cadre(titre : str):
    """Affiche un titre encadré (une liaison)

    Args:
        titre (str): titre à encadrer
    """
    print(bcolors.BOLD + "  ┌" + "─" * LARGEUR + "┐")
    print(f"  │ {titre:<{LARGEUR - 2}} │")
    print("  └" + "─" * LARGEUR + "┘" + bcolors.ENDC)


def _section(titre : str):
    """Affiche le titre d'une section à l'intérieur d'une liaison

    Args:
        titre (str): titre de la section
    """
    print(f"  {bcolors.UNDERLINE}{titre}{bcolors.ENDC}")


def _ligne(label : str, valeur, couleur : str = ""):
    """Affiche une ligne "label : valeur"

    Args:
        label (str): intitulé
        valeur: valeur à afficher
        couleur (str, optional): couleur de la valeur. Defaults to "".
    """
    fin = bcolors.ENDC if couleur else ""
    print(f"    {label:<26} : {couleur}{valeur}{fin}")


def _ligne_suite(valeur):
    """Affiche la suite d'une ligne trop longue, alignée sous la précédente

    Args:
        valeur: valeur à afficher
    """
    print(f"    {'':<26}   {valeur}")


def _apercu(cle, reference=None) -> str:
    """Construit un aperçu lisible d'une clé (les premiers bits seulement).

    Les bits qui diffèrent de la clé de référence sont affichés en rouge, et un bit jamais
    détecté (-1, l'apd n'a pas cliqué) est affiché par un point.

    Args:
        cle (list[int] | None): clé à afficher
        reference (list[int], optional): clé servant de comparaison. Defaults to None.

    Returns:
        str: aperçu de la clé suivi de sa taille
    """
    if cle is None:
        return "(aucune)"
    if len(cle) == 0:
        return bcolors.FAIL + "(vide)" + bcolors.ENDC

    texte = ""
    for i, bit in enumerate(cle[:APERCU_BITS]):
        symbole = "·" if bit == -1 else str(bit)
        if reference is not None and i < len(reference) and bit != reference[i]:
            texte += bcolors.FAIL + symbole + bcolors.ENDC
        else:
            texte += symbole
    if len(cle) > APERCU_BITS:
        texte += "…"
    return f"{texte}  ({len(cle)} bits)"


def _format_params(params : dict) -> list:
    """Met en forme les paramètres d'une variante, découpés en lignes lisibles

    Args:
        params (dict): paramètres passés à run_qkd pour cette liaison

    Returns:
        list: lignes prêtes à être affichées ([] si aucun paramètre)
    """
    if not params:
        return []

    morceaux = []
    for nom, valeur in params.items():
        morceaux.append(f"{nom}={valeur}")

    # On coupe toutes les 3 valeurs, sinon la ligne devient illisible
    lignes = []
    for debut in range(0, len(morceaux), 3):
        lignes.append(", ".join(morceaux[debut:debut + 3]))
    return lignes


def _normaliser_variantes(variantes, total : int) -> list:
    """Uniformise l'argument "variantes" de print_result en une liste de (nom, paramètres).

    On accepte une simple liste de noms ou une liste de couples (nom, paramètres), et on
    complète avec des None si la liste est plus courte que celle des résultats.

    Args:
        variantes: liste de noms ou de couples (nom, dict de paramètres), ou None
        total (int): nombre de liaisons à décrire

    Returns:
        list: liste de (nom, params) de longueur total (None quand la variante est inconnue)
    """
    normalisees = []
    for i in range(total):
        if variantes is None or i >= len(variantes):
            normalisees.append(None)
            continue

        variante = variantes[i]
        if isinstance(variante, (tuple, list)) and len(variante) == 2:
            normalisees.append((str(variante[0]), variante[1] or {}))
        else:
            normalisees.append((str(variante), {}))
    return normalisees


def _description_apd(apd) -> str:
    """Décrit la configuration d'un apd (cf. manager._make_apd)

    Args:
        apd: l'apd à décrire

    Returns:
        str: description lisible de l'apd
    """
    if apd is None:
        return "n/a"
    # C'est la signature d'un apd parfait dans manager._make_apd
    if apd.gate_off_duration == 0 and apd.dead_time_max == 0:
        return "parfait (ni gate, ni dead time)"
    return (f"gate {apd.gate_on_duration} ms ON / {apd.gate_off_duration} ms OFF, "
            f"dead time {apd.dead_time_min}-{apd.dead_time_max} ms")


r"""
  _      _       _                 
 | |    (_)     (_)                
 | |     _  __ _ _ ___  ___  _ __  
 | |    | |/ _` | / __|/ _ \| '_ \ 
 | |____| | (_| | \__ \ (_) | | | |
 |______|_|\__,_|_|___/\___/|_| |_|
"""


def _afficher_parametres(res : QkdResult, nom : str, categorie : str, variante):
    """Affiche les spécificités de l'échange (ce qui a été configuré pour cette liaison)

    Args:
        res (QkdResult): résultat de la liaison
        nom (str): nom de l'attaque
        categorie (str): catégorie de l'attaque
        variante: couple (nom, paramètres) de la variante jouée, None si inconnue
    """
    _section("Spécificités de l'échange")

    if variante is not None:
        (nom_variante, params) = variante
        _ligne("Variante", nom_variante, bcolors.OKCYAN)
        lignes = _format_params(params)
        for numero, ligne in enumerate(lignes):
            if numero == 0:
                _ligne("Paramètres forcés", ligne)
            else:
                _ligne_suite(ligne)

    _ligne("Protocole", settings.protocol)
    _ligne("Qubits émis par Alice", res.alice.message_size)

    apd_bob = getattr(res.bob, "apd0", None)
    if apd_bob is not None:
        _ligne("Période de la clock", f"{apd_bob.clock_period} ms")
    _ligne("APD de Bob", _description_apd(apd_bob))

    if res.eve is None:
        _ligne("Attaque", f"{nom} — {categorie}", bcolors.OKGREEN)
    else:
        _ligne("Attaque", f"{nom} — {categorie}", bcolors.FAIL)
        _ligne("APD d'Eve", _description_apd(getattr(res.eve, "apd0", None)))


def _afficher_transmission(res : QkdResult):
    """Affiche le déroulé de la transmission (ce qui est arrivé jusqu'à Bob)

    Args:
        res (QkdResult): résultat de la liaison
    """
    _section("Transmission")
    envoyes = res.alice.message_size

    # Un slot est marqué -1 côté base quand rien n'a été reçu à temps (cf. receiver.detect_lost_qubit)
    perdus = 0
    for base in res.bob.chosen_bases:
        if base == -1:
            perdus += 1

    # Un bit reste à -1 quand l'apd n'a jamais cliqué sur ce slot
    detectes = 0
    for bit in res.bob.measured_bits:
        if bit != -1:
            detectes += 1

    _ligne("Qubits détectés par Bob", f"{detectes}/{envoyes} ({detectes / envoyes * 100:.2f} %)"
           if envoyes else "n/a")
    _ligne("Slots perdus (base = -1)", f"{perdus} ({perdus / envoyes * 100:.2f} %)" if envoyes else perdus)
    _ligne("Bits gardés au sifting", f"{len(res.key_alice)} ({len(res.key_alice) / envoyes * 100:.2f} %)"
           if envoyes else len(res.key_alice))
    _ligne("Clé finale (post qber)", len(res.final_key))

    # Bases d'Eve : les slots où elle a lu dans la même base qu'Alice (elle y lit le bon bit)
    if res.eve is not None and not _est_statistique(res.key_eve):
        bases_eve = getattr(res.eve, "chosen_bases", [])
        bonnes = 0
        for i in range(min(len(bases_eve), len(res.alice.chosen_bases))):
            if bases_eve[i] != -1 and bases_eve[i] == res.alice.chosen_bases[i]:
                bonnes += 1
        if bonnes > 0:
            _ligne("Bases d'Eve = Alice", f"{bonnes}/{envoyes} ({bonnes / envoyes * 100:.2f} %)")


def _afficher_cles(res : QkdResult, accord, cle_eve, nb_candidates : int):
    """Affiche les clés d'Alice, Bob et Eve ainsi que leur niveau d'accord

    Args:
        res (QkdResult): résultat de la liaison
        accord (float | None): ressemblance entre les clés d'Alice et Bob, en %
        cle_eve (list[int] | None): clé d'Eve (la meilleure candidate si attaque statistique)
        nb_candidates (int): nombre de clés candidates proposées par Eve
    """
    _section("Clés")
    _ligne("Clé d'Alice", _apercu(res.key_alice))
    _ligne("Clé de Bob", _apercu(res.key_bob, res.key_alice))

    if res.eve is not None:
        # Le nombre de candidates est donné dans la section sécurité, ici le label doit rester court
        label = "Clé d'Eve" if nb_candidates <= 1 else "Clé d'Eve (la meilleure)"
        _ligne(label, _apercu(cle_eve, res.key_alice))

    if len(res.key_alice) != len(res.key_bob):
        _ligne("Tailles Alice/Bob", f"{len(res.key_alice)} vs {len(res.key_bob)} : les clés ne "
               "sont pas alignées !", bcolors.FAIL)

    erreurs = _erreurs(res.key_alice, res.key_bob)
    if res.keys_match():
        _ligne("Accord Alice/Bob", f"{_pourcent(accord)} — clés identiques", bcolors.OKGREEN)
    else:
        _ligne("Accord Alice/Bob", f"{_pourcent(accord)} — {erreurs} bit(s) divergent(s)", bcolors.WARNING)


def _afficher_securite(res : QkdResult, eve_pct, nb_candidates : int, verdict : str, couleur : str):
    """Affiche le bilan de sécurité de la liaison (qber, connaissance d'Eve, verdict)

    Args:
        res (QkdResult): résultat de la liaison
        eve_pct (float | None): part de la clé connue par Eve, en %
        nb_candidates (int): nombre de clés candidates proposées par Eve
        verdict (str): verdict de la liaison
        couleur (str): couleur associée au verdict
    """
    _section("Sécurité")
    if res.qber > settings.qber_tolerance:
        _ligne("QBER estimé", f"{res.qber:.2f} % (> tolérance {settings.qber_tolerance} %) : "
               "communication abandonnée", bcolors.FAIL)
    else:
        _ligne("QBER estimé", f"{res.qber:.2f} % (tolérance {settings.qber_tolerance} %)", bcolors.OKGREEN)

    if res.eve is None:
        _ligne("Connaissance d'Eve", "aucune (Eve n'est pas sur le canal)", bcolors.OKGREEN)
    elif eve_pct is None:
        _ligne("Connaissance d'Eve", "incalculable (clé d'Eve vide ou absente)", bcolors.WARNING)
    else:
        # En dessous de 50 % Eve fait moins bien qu'en devinant chaque bit au hasard
        gain = eve_pct - HASARD
        couleur_eve = bcolors.FAIL if eve_pct >= 90 else (bcolors.WARNING if gain > 5 else bcolors.OKGREEN)
        _ligne("Connaissance d'Eve", f"{eve_pct:.2f} % de la clé d'Alice ({gain:+.2f} pts vs hasard)",
               couleur_eve)

    # Attaque statistique : ce score est celui de la MEILLEURE candidate, encore faut-il
    # qu'Eve sache laquelle choisir. Le nombre de candidates est donc le vrai indicateur.
    if nb_candidates > 1:
        _ligne("Clés candidates d'Eve", f"{nb_candidates} (soit 1 chance sur {nb_candidates} "
               "de tomber sur la bonne)")

    _ligne("Verdict", verdict, couleur + bcolors.BOLD)


def _afficher_liaison(numero : int, total : int, res : QkdResult, variante=None) -> dict:
    """Affiche le détail complet d'une liaison

    Args:
        numero (int): numéro de la liaison dans le scénario
        total (int): nombre total de liaisons du scénario
        res (QkdResult): résultat de la liaison
        variante (optional): couple (nom, paramètres) de la variante jouée. Defaults to None.

    Returns:
        dict: les mesures de la liaison, pour le tableau récapitulatif
    """
    (nom, categorie) = _nom_attaque(res.eve)
    # Dans un scénario le nom de la variante est plus parlant que celui de l'attaque (elle ne change pas)
    etiquette = nom if variante is None else variante[0]
    print()
    _cadre(f"LIAISON {numero}/{total}  —  {nom}" + ("" if variante is None else f"  —  {variante[0]}"))

    _afficher_parametres(res, nom, categorie, variante)
    print()

    # Sans clé il n'y a plus rien à mesurer, on s'arrête là pour cette liaison
    if len(res.key_alice) == 0 or len(res.key_bob) == 0:
        print(bcolors.FAIL + f"    [ERROR] La clé d'Alice et/ou de Bob est vide "
              f"({len(res.key_alice)}, {len(res.key_bob)}) : aucune mesure exploitable" + bcolors.ENDC)
        return {"nom": etiquette, "qber": res.qber, "accord": None, "eve": None,
                "verdict": "ECHEC", "couleur": bcolors.FAIL}

    _afficher_transmission(res)
    print()

    accord = _ressemblance(res.key_alice, res.key_bob)
    (eve_pct, nb_candidates, cle_eve) = _connaissance_eve(res)
    (verdict, couleur) = _verdict(res.qber, eve_pct, res.eve is not None)

    _afficher_cles(res, accord, cle_eve, nb_candidates)
    print()
    _afficher_securite(res, eve_pct, nb_candidates, verdict, couleur)

    return {"nom": etiquette, "qber": res.qber, "accord": accord, "eve": eve_pct,
            "verdict": verdict, "couleur": couleur}


def _afficher_recapitulatif(recap : list, titre_colonne : str = "ATTAQUE"):
    """Affiche le tableau récapitulatif de toutes les liaisons du scénario

    Args:
        recap (list): mesures de chaque liaison (cf. _afficher_liaison)
        titre_colonne (str, optional): en-tête de la 2e colonne. Defaults to "ATTAQUE".
    """
    print()
    print("  ┌─────┬────────────────────────────────────┬───────────┬───────────┬───────────┬──────────────┐")
    print(f"  │ {'#':^3} │ {titre_colonne:<34} │ {'QBER':>9} │ {'CLE A/B':>9} │ {'INFO EVE':>9} │ {'VERDICT':^12} │")
    print("  ├─────┼────────────────────────────────────┼───────────┼───────────┼───────────┼──────────────┤")

    for numero, mesures in enumerate(recap, start=1):
        # On met en forme AVANT de colorer, sinon les codes couleurs décalent les colonnes
        nom = mesures["nom"] if len(mesures["nom"]) <= 34 else mesures["nom"][:33] + "…"
        verdict = f"{mesures['verdict']:^12}"
        print(f"  │ {numero:^3} │ {nom:<34} │ {_pourcent(mesures['qber']):>9} │ "
              f"{_pourcent(mesures['accord']):>9} │ {_pourcent(mesures['eve']):>9} │ "
              f"{mesures['couleur']}{verdict}{bcolors.ENDC} │")

    print("  └─────┴────────────────────────────────────┴───────────┴───────────┴───────────┴──────────────┘")


# J'arrive pas a forcer l'arg mais c'est une lsite de QkdResult
def print_result(results : list[QkdResult], variantes=None):
    """Affiche les résultats d'un scénario : pour chaque liaison ses spécificités
    (protocole, nombre de qubits, apds, attaque active), le déroulé de la transmission,
    les clés d'Alice/Bob/Eve, le qber et un verdict ; puis un tableau récapitulatif.

    Args:
        results (list[QkdResult]): liste des résultats de liaison à afficher
        variantes (optional): description de chaque liaison, dans le même ordre que results.
            Soit une liste de noms, soit une liste de couples (nom, paramètres passés à
            run_qkd). C'est ce que remplit automatiquement scenario_runner.py. Defaults to None.
    """
    # On accepte aussi un résultat seul, ça évite un plantage bête
    if isinstance(results, QkdResult):
        results = [results]

    if not results:
        print(bcolors.WARNING + "[WARN] Aucun résultat à afficher" + bcolors.ENDC)
        return

    variantes = _normaliser_variantes(variantes, len(results))

    print()
    print(bcolors.BOLD + bcolors.HEADER
          + f"  RESULTATS DU SCENARIO  |  {len(results)} liaison(s)  |  protocole {settings.protocol}"
            f"  |  tolérance QBER {settings.qber_tolerance} %" + bcolors.ENDC)

    recap = []
    for numero, result in enumerate(results, start=1):
        # Python ne vérifie pas les annotations, on fait donc un contrôle "à la main"
        if not hasattr(result, "key_alice"):
            print(bcolors.FAIL + f"  [ERROR] La liaison n°{numero} n'est pas un QkdResult "
                  f"({type(result).__name__}), elle est ignorée" + bcolors.ENDC)
            continue
        recap.append(_afficher_liaison(numero, len(results), result, variantes[numero - 1]))

    if recap:
        _afficher_recapitulatif(recap, "VARIANTE" if variantes[0] is not None else "ATTAQUE")
    print()

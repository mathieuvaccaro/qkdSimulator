r"""
Attention, l'execution peut prendre du temps. 
Dernier résultat en date (11/06/26)
QKD-SIM  benchmark d'attaques  |  protocole bb84  |  n = 200 qubits  |  3 run(s) par attaque

"""

import settings
import manager
from utils.colors import bcolors
from utils.percent_corrupted_key import how_much_key_corrupted

RUNS = 3                # Nombre de communications par attaque

"""
  ┌─────┬───────────────────────────┬──────────────────────────────────┬───────────┬───────────┬───────────┬──────────┐
  │  #  │ ATTAQUE                   │ CATEGORIE                        │      QBER │   CLE A/B │  INFO EVE │ VERDICT  │
  ├─────┼───────────────────────────┼──────────────────────────────────┼───────────┼───────────┼───────────┼──────────┤
  │  1  │ Intercept-Resend          │ Mesure directe / individuelle    │   23.39 % │   75.61 % │   73.97 % │ DETECTEE |
  │  2  │ Photon Number Splitting   │ Source / multi-photon            │    3.70 % │   96.38 % │   98.65 % │ CRITIQUE |
  │  3  │ Trojan Horse              │ Canal auxiliaire (side-channel)  │    5.00 % │   96.02 % │   97.38 % │ CRITIQUE |
  │  4  │ Double Click Event        │ Detecteur / double click         │    2.78 % │   96.17 % │   94.54 % │ CRITIQUE |
  │  5  │ Time Correlation          │ Detecteur / dead time (stat.)    │    1.75 % │   96.12 % │   61.23 % │ INOFFENSIVE |
  └─────┴───────────────────────────┴──────────────────────────────────┴───────────┴───────────┴───────────┴──────────┘
  """


# Flags d'attaque de settings.py (miroir de ATTACK_REGISTRY dans attacks/attack_manager.py)
ATTACK_FLAGS = ["INTERCEPT_AND_RESENT", "PNS", "TROJAN_HORSE", "DOUBLE_CLICK_EVENT", "TIME_CORRELATION"]

# Scénario Nom, Catégorie, Attaque, Paramètres
SCENARIOS = [
    ("Intercept-Resend", "Mesure directe / individuelle", "INTERCEPT_AND_RESENT", {}),
    ("Photon Number Splitting", "Source / multi-photon", "PNS", {"average_emitted_photon": 1.0}),
    ("Trojan Horse", "Canal auxiliaire (side-channel)", "TROJAN_HORSE", {}),
    ("Double Click Event", "Detecteur / double click", "DOUBLE_CLICK_EVENT", {"perfect_apd_bob": False, "dead_time_min": 2, "dead_time_max": 3}),
    ("Time Correlation", "Detecteur / dead time (stat.)", "TIME_CORRELATION", {"perfect_apd_bob": False, "dead_time_min": 20, "dead_time_max": 60}),
]


def config(flag : str, reglages : dict):
    """Permet de configurer les paramètres des attaques

    Args:
        flag (str): flag de l'attaque à activer
        reglages (dict): réglages propres à l'attaque, qui écrasent la configuration commune
    """
    # On pars d'un modèle "parfait" et on va changer les paramètres au fur et a mesure des attaques
    settings.message_size = 5000
    settings.message_interval = 4
    settings.tolerance_message_not_receive = settings.message_interval - 0.2
    settings.average_emitted_photon = 0.1
    settings.perfect_apd_bob = False
    settings.perfect_apd_eve = True #Malgrés des settings réaliste, on suppose que eve a la meillrue techno possible
    settings.quantum_canal_bit_loss = 37.0
    settings.quantum_canal_bit_flip = 1.3
    settings.gate_off_duration = 2e-6      # Même convention que test/attacks/manager_test.py
    settings.gate_on_duration = 9.98e-4
    settings.dead_time_min = 0.008
    settings.dead_time_max = 0.0012
    settings.many_clicks_gestion = "THROWS"
    settings.emission_click_event = 10
    settings.timing_attack = 30
    settings.progress_bar = False       # La barre de progression n'a pas sa place dans un bench

    # Parcours l'intégralité des settings 
    for nom, valeur in reglages.items():
        setattr(settings, nom, valeur)

    for f in ATTACK_FLAGS:
        setattr(settings, f, f == flag)

def lancer(flag : str, reglages : dict) -> dict:
    """Joue une communication complète et récupère ses mesures

    Args:
        flag (str): flag de l'attaque à activer
        reglages (dict): réglages propres à l'attaque

    Returns:
        dict: mesures du run (qber, accord Alice/Bob, part de clé connue par Eve, durée...)
    """
    config(flag, reglages)

    res = manager.run_communication()

    # Cas particulier, le time correlation, l'attauqe nous retourne une liste de solution
    if flag == "TIME_CORRELATION":
        eve = 0
        for candidat in res.key_eve:
            score = how_much_key_corrupted(res.final_key, candidat)
            if score > eve:
                eve = score
    else:
        eve = how_much_key_corrupted(res.key_alice, res.key_eve)

    return {"qber": res.qber,
            "accord": how_much_key_corrupted(res.key_alice, res.key_bob),
            "eve": eve}


# Détecté : qber au dessus de seuil
# Critique : eve a bcp d'information et qber est nettement dessosu du seil
# Suspect : eve a bcp d'information et qber est juste en dessous du seil
# Innofensif : eve ne sait rien de plus que le hasard
def verdict(qber : float, eve : float):
    """Permet de mettre un score a l'attaque

    Args:
        qber (float): QBER moyen, en %
        eve (float): part de la clé connue par Eve, en %

    Returns:
        tuple: (verdict, couleur)
    """
    if qber > settings.qber_tolerance:
        return (bcolors.OKCYAN + "DETECTEE" + bcolors.ENDC)       # Alice et Bob abandonnent la communication
    if eve >= 90:
        return (bcolors.FAIL + "CRITIQUE" + bcolors.ENDC)       # Invisible ET Eve a (presque) toute la clé
    if qber >= settings.qber_tolerance / 2:
        return (bcolors.WARNING + "SUSPECTE" + bcolors.ENDC)    # Sous la tolérance mais anormalement haut
    return (bcolors.OKGREEN + "INOFFENSIVE" + bcolors.ENDC)


def afficher_tableau(resultats : list):
    """Affiche le tableau récapitulatif du benchmark

    Args:
        resultats (list): liste de (nom, catégorie, flag, réglages, moyennes)
    """
    # Le tableau a été fait à l'aide d'une ia pour le rendre plus joli :)
    print()
    print("  ┌─────┬───────────────────────────┬──────────────────────────────────┬───────────┬───────────┬───────────┬──────────┐")
    print(f"  │ {'#':^3} │ {'ATTAQUE':<25} │ {'CATEGORIE':<32} │ {'QBER':>9} │ {'CLE A/B':>9} │ {'INFO EVE':>9} │ {'VERDICT':^8} │")
    print("  ├─────┼───────────────────────────┼──────────────────────────────────┼───────────┼───────────┼───────────┼──────────┤")

    for numero, (nom, categorie, _, _, m) in enumerate(resultats, start=1):
        etiquette = verdict(m["qber"], m["eve"])
        qber = f"{m['qber']:.2f} %"
        accord = f"{m['accord']:.2f} %"
        eve = f"{m['eve']:.2f} %"
        print(f"  │ {numero:^3} │ {nom:<25} │ {categorie:<32} │ {qber:>9} │ {accord:>9} │ {eve:>9} │ "
             + f"{etiquette:^10} |")

    print("  └─────┴───────────────────────────┴──────────────────────────────────┴───────────┴───────────┴───────────┴──────────┘")

if __name__ == "__main__":
    print(f"  QKD-SIM  benchmark d'attaques  |  protocole {settings.protocol}  |  "
          f"n = {settings.message_size} qubits  |  {RUNS} run(s) par attaque")
    print()

    resultats = []

    for (nom, categorie, flag, reglages) in SCENARIOS:
        print(f"  Test de {nom}", end="", flush=True)

        runs = []
        for i in range(RUNS):
            runs.append(lancer(flag, reglages))
            print(".", end='', flush=True)
        print("")
        moyennes = {}
        for mesure in runs[0]:
            total = 0
            for run in runs:
                total += run[mesure]
            moyennes[mesure] = total / RUNS
        resultats.append((nom, categorie, flag, reglages, moyennes))

    afficher_tableau(resultats)

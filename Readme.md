# scenarios/

Des scénarios prêts à lancer, pour jouer une attaque dans plusieurs configurations
**sans jamais éditer `settings.py` à la main**.

```bash
python3 scenarios/scenarios_sans_attaque.py
python3 scenarios/scenarios_intercept_and_resent.py
python3 scenarios/scenarios_pns.py
python3 scenarios/scenarios_trojan_horse.py
python3 scenarios/scenarios_double_click_event.py
python3 scenarios/scenarios_time_correlation.py
```

Chaque scénario joue la même attaque sur plusieurs **variantes** (des jeux de paramètres),
puis affiche pour chaque liaison : les spécificités de l'échange, le déroulé de la
transmission, les clés d'Alice/Bob/Eve, le QBER et un verdict, avant un tableau
récapitulatif. Comptez une dizaine de secondes par scénario.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `scenarios_*.py` | un scénario par attaque : c'est là qu'on écrit les variantes |
| `scenario_runner.py` | le moteur commun (joue les variantes, arrête les threads, appelle l'affichage) |
| `print_results.py` | l'affichage des résultats (`print_result(results)`) |
| `manager_scenario.py` | `run_qkd(...)`, le raccourci qui écrit dans `settings.py` à notre place |
| `confscenario.py` | sauvegarde/restauration des settings (fixture pytest) |

## Écrire un nouveau scénario

```python
ATTAQUE   = "INTERCEPT_AND_RESENT"          # cf. attacks/attack_manager.py, None = aucune

COMMUN    = {"message_size": 300,           # appliqué à toutes les variantes
             "message_interval": 4}

VARIANTES = [("Référence sans Eve", {"attack": None}),   # "attack" coupe/change l'attaque
             ("Canal bruité",       {"bit_flip": 3.0})]  # écrase COMMUN

run_scenario(TITRE, DESCRIPTION, ATTAQUE, VARIANTES, COMMUN)
```

Tous les paramètres acceptés sont ceux de `run_qkd` (`manager_scenario.py`) : taille et
cadence du message, source (`average_emitted_photon`), bruit du canal (`bit_loss`,
`bit_flip`), apds (`perfect_apd`, `gate_*`, `dead_time_*`, `after_pulsing`), gestion des
doubles clicks (`many_clicks_gestion`, `emission_click_event`), budget d'Eve
(`timing_attack`), échantillon du QBER (`qber_percent`).

## Attention

- Une variante qui plante n'arrête pas le scénario : l'erreur est affichée et on passe à
  la suivante.
- `PNS` exige une source imparfaite (`average_emitted_photon` différent de `-1`).
- `DOUBLE_CLICK_EVENT` exige des apds avec un dead time côté Bob, sinon toute la rafale
  d'Eve clique et Bob jette l'intégralité de la clé.
- `TIME_CORRELATION` énumère 2^C clés candidates : garder une clé courte et un
  `timing_attack` de quelques secondes, sinon l'énumération part très loin.


# Tester le programme

- Lancer tous les tests : `pytest`
- Lancer les tests d'une attaque spécifique : `pytest <Adresse du fichier test>`
- Lancer tous les tests *n* fois : `pytest --count=n`
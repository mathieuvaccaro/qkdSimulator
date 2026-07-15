import os
import sys
from dataclasses import dataclass
from typing import Optional

import settings
import components.clock as clock
import components.qber as qber
import components.sifting as sifting
from components.apd import Apd
from components.quantum_canal import QuantumCanal
from components.receiver import Receiver
from components.sender import Sender
from attacks.attack_manager import get_active_attack
from utils.colors import bcolors
from utils.percent_corrupted_key import how_much_key_corrupted

"""
Le simulateur fonctionne grâce a une clock global. Dans un cas réel il faudrait utilisé deux clocks distinctes synchronisé, mais bon personne n'est parfait....
"""


def restart():
    """Tout oublier : (Angèle, 2018)"""
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable] + sys.argv)

@dataclass # Le module dataclass permet de ne pas a avoir à créer d'init quand l'init est l'intégralité des paramètres (j'adore)
class QkdResult:
    """Résultat d'une communication QKD complète."""

    alice: Sender
    bob: Receiver
    eve: Optional[object]        # intercepteur (None si aucune attaque n'est active)
    key_alice: list[int]         # clé siftée d'Alice
    key_bob: list[int]           # clé siftée de Bob
    key_eve: Optional[list[int]]  # clé reconstruite par Eve (None sans attaque)
    final_key: list[int]         # clé d'Alice une fois les bits du QBER retirés
    qber: float                  # QBER estimé sur un échantillon aléatoire, en %

    def alice_len(self) -> int:
        return len(self.key_alice)

    def keys_match(self) -> bool:
        """True si Alice et Bob obtiennent EXACTEMENT la même clé."""
        return self.key_alice == self.key_bob

    def n_errors(self) -> int:
        """Nombre de bits différents entre la clé d'alice et bob."""
        if(len(self.key_alice) != len(self.key_bob)):
            raise Exception(bcolors.FAIL + "[ERROR] Les clés ne sont pas de taille identiques..." + bcolors.ENDC)
        compteur = 0
        for i in range(len(self.key_alice)):
            if(self.key_alice[i] != self.key_bob[i]):
                compteur += 1
        return compteur

    def eve_knowledge(self) -> Optional[float]:
        """Pourcentage des bits de la clé d'Alice retrouvés par Eve (None sans attaque). """
        if self.key_eve is None:
            return None
        
        if(len(self.key_eve) != len(self.key_alice)):
            raise Exception("La clé d'eve n'a pas la même taille que la clé d'Alice")
        
        compteur = 0
        for i in range(len(self.key_eve)):
            if(self.key_eve[i] == self.key_alice[i]):
                compteur +=1
        return compteur / len(self.key_eve) * 100

def _make_apd(linked_bit: int, perfect_apd : bool) -> Apd:
    """Crée un APD, dans la configuration de settings.py

    Args:
        linked_bit (int): bit associé au détecteur (0 ou 1)
        perfect_apd : étant donné que la perfection des apds diffèrent entre bob et eve, on doit le passer en paramètre

    Returns:
        Apd: le détecteur configuré
    """
    if perfect_apd:
        return Apd(linked_bit, clock_period=settings.message_interval,
                   gate_off_duration=0, gate_on_duration=1000, dead_time_min=0, dead_time_max=0)

    return Apd(linked_bit=linked_bit,
               clock_period=settings.message_interval,
               gate_off_duration=settings.gate_off_duration,
               gate_on_duration=settings.gate_on_duration,
               dead_time_min=settings.dead_time_min,
               dead_time_max=settings.dead_time_max)


def build_communication():
    """Câble tous les composants d'une communication (canal, clock, APDs, Alice, Bob, Eve). Aucun thread n'est lancé 

    Returns:
        tuple: (alice, bob, eve, commune_clk, apds) ; eve vaut None si aucune attaque n'est active
    """
    quantum_canal = QuantumCanal()

    # Alice et Bob utilisent une clock commune, ici elle est dans le manager.py, mais l'idée finale est de la faire communiquer grâce a un canal publique
    commune_clk = clock.Clock(settings.message_interval)

    apd0 = _make_apd(0, settings.perfect_apd_bob)
    apd1 = _make_apd(1, settings.perfect_apd_bob)

    # Création des entités
    alice = Sender(quantum_canal, commune_clk)
    bob = Receiver(apd0, apd1, quantum_canal, commune_clk)

    # Canal de communication
    quantum_canal.setSender(alice)
    quantum_canal.setReceiver(bob)

    # Assigner les apd a bob 
    apd0.set_parent(bob)
    apd1.set_parent(bob)
    commune_clk.subscribe(bob.prepare_bases)
    commune_clk.subscribe(alice.emit_qubit)
    commune_clk.subscribe(bob.detect_lost_qubit)

    # Ajouter la gestion de clés
    commune_clk.subscribe(bob.addBitToKey)

    apds = [apd0, apd1]
    eve = None

    # Select attack
    AttackClass = get_active_attack()
    if AttackClass is not None:
        apd_eve0 = _make_apd(0, settings.perfect_apd_eve)
        apd_eve1 = _make_apd(1, settings.perfect_apd_eve)
        eve = AttackClass(apd_eve0, apd_eve1, quantum_canal, commune_clk, alice, bob)

        quantum_canal.setInterceptor(eve)
        apd_eve0.set_parent(eve)
        apd_eve1.set_parent(eve)
        apds += [apd_eve0, apd_eve1]

    return alice, bob, eve, commune_clk, apds


def run_communication() -> QkdResult:
    """Lance la communication complète

    Returns:
        QkdResult: clés d'Alice/Bob/Eve et métriques associées
    """
    alice, bob, eve, commune_clk, apds = build_communication()

    # Démarrage des apd
    for a in apds:
        a.run()

    # Démarrage de clock (qui démarre tout le système)
    commune_clk.start()
    alice.communication_finished.wait()
    bob.communication_finished.wait()

    key_alice = sifting.sifting(alice, bob.chosen_bases)  # Pour l'instant on passe tout par manager.py, mais a terme il faudrait simuler une sorte de connexion et de synchornisation
    key_bob = sifting.sifting(bob, alice.chosen_bases)
    (qber_value, final_key) = qber.qber_calculus(key_alice, key_bob)

    key_eve = None
    if eve is not None:
        # Eve exploite les bases d'Alice, publiques une fois la communication finie
        eve.resolve_knowledge(alice.chosen_bases)
        key_eve = sifting.eve_sifting(eve, alice.chosen_bases, bob.chosen_bases)

    return QkdResult(alice, bob, eve, key_alice, key_bob, key_eve, final_key, qber_value)


def print_report(res: QkdResult):
    """Affiche le bilan d'une communication (clés, QBER, connaissance d'Eve)

    Args:
        res (QkdResult): résultat renvoyé par run_communication()
    """
    if(len(res.key_alice) == 0 or len(res.key_bob) == 0):
        print(bcolors.FAIL + f"[ERROR] La clé d'alice et/ou de bob est vide ({len(res.key_alice)}, {len(res.key_bob)})" + bcolors.ENDC)
        return

    if(len(res.key_alice) != len(res.key_bob)):
        print(bcolors.FAIL + f"[ERROR] Alice and bob haven't same keys size ! ({len(res.key_alice)} vs {len(res.key_bob)})" + bcolors.ENDC)
    elif(not res.keys_match):
        print(bcolors.WARNING + f"[WARN] Alice and bob haven't same keys (taille = {len(res.key_alice)} et ({how_much_key_corrupted(res.key_alice, res.key_bob)}%)" + bcolors.ENDC)
    else:
        print(bcolors.OKGREEN + f"[GOOD] Alice and bob have same keys (taille de la clé : {len(res.key_alice)}!" + bcolors.ENDC)

    if(res.qber < settings.qber_tolerance):
        print(bcolors.OKGREEN + f"[GOOD] Alice and Bob have a good qber value ({res.qber})%" + bcolors.ENDC)
    else:
        print(bcolors.FAIL + f"Qber is very high : {res.qber}. Communication aborting ..." + bcolors.ENDC)

    if(res.eve != None):
        if(len(res.key_eve) != len(res.key_alice)):
            print(bcolors.WARNING + f"Alice and Eve size's key aren't same :" + bcolors.ENDC)
        print(bcolors.FAIL + f"Eve got {how_much_key_corrupted(res.final_key, res.key_eve)} % of Alice key" + bcolors.ENDC)

# Lancemnet classique
if __name__ == "__main__":
    while(True):
        print("Initialisation en cours...")
        print("Lancement ...")
        print_report(run_communication())
        restart()

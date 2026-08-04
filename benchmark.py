from utils.colors import bcolors
from manager import run_communication

value = """
QKD-SIM  benchmark d'attaques  |  protocole BB84  |  n = 10^6 qubits  |  seuil 11%

  ┌─────┬───────────────────────────┬──────────────────────────────────┬───────────┬───────────┬───────────┬────────────┐
  │  #  │ ATTAQUE                   │ CATEGORIE                        │      QBER │   CLE A/B │  INFO EVE │  VERDICT   │
  ├─────┼───────────────────────────┼──────────────────────────────────┼───────────┼───────────┼───────────┼────────────┤
  │  1  │ Intercept-Resend          │ Mesure directe / individuelle    │   25.00 % │   75.00 % │   50.00 % │  DETECTEE  │
  │  2  │ Beam Splitting            │ Canal optique / passive          │    0.20 % │   99.80 % │    4.80 % │  FURTIVE   │
  │  3  │ Photon Number Splitting   │ Source / multi-photon            │    0.40 % │   99.60 % │   42.00 % │  SUSPECTE  │
  │  4  │ Trojan Horse              │ Canal auxiliaire (side-channel)  │    0.60 % │   99.40 % │   31.00 % │  SUSPECTE  │
  │  5  │ Detector Blinding         │ Detecteur / faked-state          │    2.80 % │   97.20 % │   96.50 % │  CRITIQUE  │
  └─────┴───────────────────────────┴──────────────────────────────────┴───────────┴───────────┴───────────┴────────────┘
  """

def benchmark_manager(attacks, protocol = "bb84", qubits_number = 10**6):
    print(bcolors.OKBLUE + "Benchmark QKDSimulator" + bcolors.ENDC)
    print(f"Stats : protocole : {protocol} | n = {qubits_number}")



    print("┌─────┬───────────────────────────┬───────────┬───────────┬───────────┬────────────┐")
    print("│  #  │ ATTAQUE                   │      QBER │   CLE A/B │  INFO EVE │  VERDICT   │")
    print("├─────┼───────────────────────────┼───────────┼───────────┼───────────┼────────────┤")
    for i in range(len(attacks)):
        report = run_communication(attacks[i])
        print(f"│  {i}  │ {attacks[i]}          │   {report.qber} % │   {report.keys_match} % │   {report.eve_knowledge} % │  DETECTEE  │")
        
    print("└─────┴───────────────────────────┴───────────┴───────────┴───────────┴────────────┘")

attacks = ["INTERCEPT_AND_RESENT", "PNS", "TROJAN_HORSE", "DOUBLE_CLICK_EVENT", "TIME_CORRELATION"]
benchmark_manager(attacks)


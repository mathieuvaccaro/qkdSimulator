import settings
from protocols import bb84 #, b92 ...

def get_states():
    # Pour l'instant on retourne uniquemnt le states, mais l'idée est de pouvoir retourner toutes les infos des protocoles (bases et vercteurs utilisés...)
    match(settings.protocol):
        case "bb84":
            return (bb84.get_states())
import settings

# Il est 16h40 et j'ai pas le courage de commencer les attaques....
taille = 40

def progress_bar(valeur_actuelle : int, valeur_total : int):
    """Juste une progress bar (vibe coder mais faut pas le dire)

    Args:
        valeur_actuelle (int): Nombre de bits transmit depuis le début à l'instant t
        valeur_total (int): Nombre de bits a transmettre au total
    """    
    if(not(settings.progress_bar)):
        return
    if valeur_total == 0:
        return
    fraction = valeur_actuelle / valeur_total
    filled = int(taille * fraction)
    bar = "█" * filled + "-" * (taille - filled)
    largeur = len(str(valeur_total))
    print(f"\r|{bar}| {fraction:.0%} ({valeur_actuelle:>{largeur}}/{valeur_total})", end="", flush=True)
    if valeur_actuelle >= valeur_total:
        print()  # saut de ligne final dès qu'on atteint (ou dépasse) le total
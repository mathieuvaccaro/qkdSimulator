def how_much_key_corrupted(keyA : list[int], keyB : list[int]):
    """Permet de savoir la différence en pourcentage des deux listes

    Args:
        keyA (list[int]): Liste 1
        keyB (list[int]): Liste 2

    Returns:
        _type_: Retourne le pourcentage de ressemblance des deux listes
    """    
    if(len(keyA) != len(keyB)):
        return 0
    else:
        value = 0
        for i in range(len(keyA)):
            if(keyA[i] == keyB[i]):
                value += 1
        return value / len(keyA) * 100  
        
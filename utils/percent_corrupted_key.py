def how_much_key_corrupted(keyA, keyB):
    if(len(keyA) != len(keyB)):
        print("Key aren't same size")
        print(f" A : {len(keyA)} alors que B : {len(keyB)}")
        return 0
    else:
        value = 0
        for i in range(len(keyA)):
            if(keyA[i] == keyB[i]):
                value += 1
        return value / len(keyA) * 100  
        
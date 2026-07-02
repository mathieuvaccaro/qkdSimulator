import receiver
import sender

from utils.colors import bcolors

# Redirection if self is sender or receiver
def sifting(self, other_bases):
    if(isinstance(self, receiver.Receiver)):
        return sifting_receiver(self, other_bases)
    else:
        return sifting_sender(self, other_bases)


def sifting_receiver(self : receiver.Receiver, other_bases):
    key = []
    if(len(other_bases) != len(self.receiver_basis)):
        print(bcolors.WARNING + "Basis aren't same length ! communication aborting")
        return False
    
    for i in range(len(other_bases)):
        # Same basis used
        if(other_bases[i] == self.receiver_basis[i]):
            key.append(self.receiver_bits[i])

    return key

def sifting_sender(self : sender.Sender, other_bases):
    key = []

    if(len(other_bases) != len(self.sending_basis)):
        print(bcolors.WARNING + "Basis aren't same length ! communication aborting")
        return False
    
    for i in range(len(other_bases)):
        # Same basis used
        if(other_bases[i] == self.sending_basis[i]):
            key.append(self.sending_bits[i])

    return key


import qutip
from utils.colors import bcolors
from intercept.factory import Intercept
import settings

class Pns(Intercept):
    """L'attaque PNS repose sur le principe suivant :
    L'emetteur émet plus d'un photon en moyenne,
    Lorsque un seul photon est émis, eve le détruit,
    Lorsque plus d'un photon est émis, eve en garde un pour elle et laisse passer le(s) autre(s) tel quel
    Eve n'a plus qu'à attendre l'étape de sifting pour lire le photon dans la bonne base.

    QBER Estimé : 0%
    Clé Estimé : dépend du nombre de photons émis
    Détectable : Non

    Args:
        Intercept (_type_): Héritage de factory.py dans intercept
    """    

    def __init__(self, apdEve0, apdEve1, quantum_canal, commune_clk, Alice, Bob):
        print(bcolors.OKCYAN + "[ATTACK PNS] ..." + bcolors.ENDC)
        super().__init__(apdEve0, apdEve1, quantum_canal, commune_clk)
        self.alice = Alice
        self.kept_states = [None] * self.message_size
        self.chosen_bases = [-1] * self.message_size
        self.measured_bits = [-1] * self.message_size
        self.last_tick = -1     
        self.photon_count = 0 

        if(settings.average_emitted_photon == -1):
            raise Exception("Attention, l'attaque PNS ne peux pas être effectué sur un canal parfait.")

    def receive_qubit(self, sent_state : qutip.Qobj):
        """Réception des qubits appelé par le canal quantique

        Args:
            sent_state (qutip.Qobj): Bit (binaire) final lu par l'apd
        """        
        # Permet de bloquer le mutex
        with self._lock:
            idx = len(self.alice.chosen_bases) - 1
            if(idx != self.last_tick): 
                self.last_tick = idx
                self.photon_count = 0
            self.photon_count += 1

            if(self.photon_count == 1):
                # 1er photon -> le photon est gardé et préserver. Il sera utilisé pour la clé si il y en a plusieurs sinon il sera annulé durant le sifting publique de alice et bob
                if(0 <= idx < len(self.kept_states)):
                    self.kept_states[idx] = sent_state
            elif(self.photon_count == 2):
                # 2e photon -> pulse MULTI-photon : Eve transmet ce photon tel quelle a Bob
                self.send_qubit(sent_state)
            # Au dela de 2 photons -> Eve ne le transmets pas

    def detect_lost_qubit(self):   
        """Dans le cas de l'attaque PNS, c'est eve qui controle quelle bit passe et ne passe pas, il n'y a donc pas besoins de mesure de bit erroné 
        """            
        pass

    def already_receive_photon(self, *args):
        """Déjà gérer dans receive_qubit
        """
        pass

    def resolve_knowledge(self, alice_bases):
        """Mesure a posteriori des photons prélevés par Eve.

        Appelée une fois la communication terminée, quand les bases d'Alice sont
        publiques. Eve mesure chaque photon conservé (kept_states) dans la bonne
        base d'Alice : elle obtient donc le bit exact sans erreur. Le résultat
        remplit measured_bits, utilisé ensuite par le eve_sifting.

        Args:
            alice_bases (list[int]): bases d'Alice, révélées publiquement (-1 si slot ignoré).
        """
        for i in range(self.message_size):
            state = self.kept_states[i]
            if(state is not None and i < len(alice_bases) and alice_bases[i] != -1):
                b = alice_bases[i]
                s0 = qutip.ket2dm(self.STATES[(0, b)])
                s1 = qutip.ket2dm(self.STATES[(1, b)])
                self.measured_bits[i] = qutip.measurement.measure(state, [s0, s1])[0]

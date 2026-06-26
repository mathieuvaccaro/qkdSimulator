import threading
import time

# Class Receiver represente an APD in Gated Mode.
# Each APD is linked with bit (linked_bit)

# To simplify, we gonna use only "classic" physic. No superposition, no photon etc.
# We're gonna approx quantum circuti with electronical circuit.

def approx_Equal(x, y, tolerance=0.001):
    return abs(x-y) <= 0.5 * tolerance * (x + y)

class Apd:

    t = 0 #  t
    is_running = True
    # Linked_bit is bit of detector (0 or 1)
    # seuil_claquage : V_br
    # temps_mort : Dead time before two detected photon
    # Tension_constante : V_dc < V_br /!\
    # Tension gate
    # Duree_detection correspond a la durée d'activation du mode geiger en tick d'hologe
    # periode_detection correspond a la période de détection entre deux détection (de la fin de la premiere au début de la deuième) en tick d'horloge
    # horloge : L'horloge interne simulé (en ms)
    def __init__(self, linked_bit, seuil_claquage = 7, temps_mort = 30, tension_constante = 5, tension_gate = 5, duree_detection = 2, periode_detection = 2, horloge = 10):
        
        if(tension_constante + tension_gate < seuil_claquage):
            print("ERROR : Il faut que la tenison constant + tensions gate > seuil claquage")
            return False
        
        self.mode = "linear"
        self.tension_constante = tension_constante
        self.tension_gate = tension_gate
        self.seuil_claquage = seuil_claquage # Tension de claquage en V

        self.bit_received = False
        self.linked_bit = linked_bit

        self.temps_mort = temps_mort # ns 

        self.duree_detection = duree_detection
        self.periode_detection = periode_detection

        self.horloge = horloge

        self.Vapd = self.tension_constante

        self.detection = False

    def clock(self):
        while(self.is_running):
            time.sleep(self.horloge/1000)
            
            # Just in cas overflow
            try:
                self.t+=1
            except:
                self.t=0
            self.callback_gestion()

    # this functino is called for each tic
    def callback_gestion(self):
        self.update_tension()
        self.mode_manager()
        self.detection_manager()

    # Just a thread manager
    def run(self):
        Tclock = threading.Thread(target=apd.clock)
        Tclock.start()
        print("Horloge de l'APD lancé")
        Tclock.join()



    # Method to switch mode
    def mode_manager(self):
        # Switch to geiger mode
        if(self.Vapd > self.seuil_claquage):
            if(self.mode == "linear"):
                self.mode = "geiger"
        else:
            if(self.mode == "geiger"):
                self.mode = "linear"


    def detection_manager(self):
        # Détection
        if(approx_Equal(self.t % (self.periode_detection + self.duree_detection), 0)):
            self.detection = True

        # Pas de détection
        elif(approx_Equal(self.t % (self.periode_detection + self.duree_detection), self.duree_detection)):
            self.detection = False


    # get and update vapd
    def update_tension(self):
        # in geiger mode
        if(self.detection == True):
            self.Vapd = self.tension_constante + self.tension_gate
        else:
            self.Vapd = self.tension_constante
        print(f"Tension : {self.Vapd}")

    # Pour l'instna la detection se fait automatiquement (a condition que le mode soit geiger et en détection)
    #def detect_photon(self):


apd = Apd(1, horloge=100)
apd.run()
print("Thread lancé ")
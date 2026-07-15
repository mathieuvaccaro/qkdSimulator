import threading
import time
from typing import Callable

"""
La clock permet la synchronisation de tout le projet, pour ajouter une fonction a la clock qui sera automatiquement appelé de manière synchrone il faut
appele la fonction subscribe avec la fonction
"""

class Clock:
    def __init__(self, interval_ms: float):
        """Initialise la clock avec sa période de tick

        Args:
            interval_ms (float): période entre deux ticks, en ms
        """
        self.interval_ms = interval_ms              # période en ms
        self._interval_s = interval_ms / 1000.0     # version interne en s
        self._callbacks: list[Callable[[], None]] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._start_time: float | None = None       # en s (monotonic)
        self._tick_count = 0

    def subscribe(self, fn: Callable[[], None]):
        """Ajout une fonction dans la liste d'abonnement

        Args:
            fn (Callable[[], None]): adresse de fonction
        """        
        with self._lock:
            self._callbacks.append(fn)

    def elapsed(self) -> float:
        """Permet de récupérer le temps écoulé depuis le lancement

        Returns:
            float: Temps écoulé en ms, 0.0 si pas démarée
        """        
        if self._start_time is None:
            return 0.0
        return (time.monotonic() - self._start_time) * 1000.0

    def _run(self):
        """Boucle principale du thread : déclenche un tick à chaque période
        """
        next_tick = time.monotonic()                # en s
        while not self._stop_event.is_set():
            self._tick()
            self._tick_count += 1
            next_tick += self._interval_s           # arithmétique en s
            delay = next_tick - time.monotonic()
            if delay > 0:
                self._stop_event.wait(delay)

    def _tick(self):
        """Exécute à chaque tick toutes les fonctions abonnées
        """
        with self._lock:
            callbacks = list(self._callbacks)
        for fn in callbacks:
            fn()
            #try:
            #    fn()
            #except Exception as e:
            #    print(f"Erreur dans {fn.__name__}: {e}")

    def start(self):
        """Démarre la clock dans un thread dédié
        """
        self._stop_event.clear()
        self._start_time = time.monotonic()
        self._tick_count = 0
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self, timeout: float | None = None):
        """Demande l'arrêt de la clock : la boucle sortira après avoir terminé le tick courant

        Args:
            timeout (float | None, optional): temps max d'attente lors du join du thread. Defaults to None.
        """
        # On demande l'arrêt : la boucle _run sortira APRÈS avoir terminé le tick
        # courant (donc tous les callbacks déjà entamés vont jusqu'au bout).
        self._stop_event.set()

        t = self._thread
        if t is None:
            return

        if threading.current_thread() is t:
            return

        t.join(timeout)
        self._thread = None
        self._start_time = None
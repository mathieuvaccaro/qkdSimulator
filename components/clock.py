import threading
import time
from typing import Callable

class Clock:
    def __init__(self, interval_ms: float):
        self.interval_ms = interval_ms              # période en ms (API publique)
        self._interval_s = interval_ms / 1000.0     # version interne en s
        self._callbacks: list[Callable[[], None]] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._start_time: float | None = None       # en s (monotonic)
        self._tick_count = 0

    def subscribe(self, fn: Callable[[], None]):
        with self._lock:
            self._callbacks.append(fn)

    def unsubscribe(self, fn: Callable[[], None]):
        with self._lock:
            self._callbacks.remove(fn)

    # --- API publique de lecture du temps (en ms) ---
    def elapsed(self) -> float:
        #Temps réel écoulé (ms) depuis start(). 0.0 si pas démarrée.
        if self._start_time is None:
            return 0.0
        return (time.monotonic() - self._start_time) * 1000.0

    def _run(self):
        next_tick = time.monotonic()                # en s
        while not self._stop_event.is_set():
            self._tick()
            self._tick_count += 1
            next_tick += self._interval_s           # arithmétique en s
            delay = next_tick - time.monotonic()
            if delay > 0:
                self._stop_event.wait(delay)        # wait() attend des secondes

    def _tick(self):
        with self._lock:
            callbacks = list(self._callbacks)
        for fn in callbacks:
            try:
                fn()
            except Exception as e:
                print(f"Erreur dans {fn.__name__}: {e}")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._start_time = time.monotonic()
        self._tick_count = 0
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self, timeout: float | None = None):
        # Nothing to do if clock is not running
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.set()
            return

        self._stop_event.set()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout)
        self._thread = None
        self._start_time = None
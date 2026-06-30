import threading
import time
import clock  # We use clock.py
from utils.colors import bcolors

# Class APD represents an avalanche photodiode in Gated Mode.
# Each APD is linked with a bit (linked_bit)

# To simplify, we use only "classic" physics. No superposition, no photon, etc.
# We approximate the quantum circuit with an electronic circuit.


def approx_equal(x, y, tolerance=0.001):
    if x + y == 0:
        return abs(x - y) <= tolerance
    return abs(x - y) <= 0.5 * tolerance * abs(x + y)


class Apd:

    # linked_bit         : bit of the detector (0 or 1)
    # breakdown_voltage  : V_br (in V)
    # dead_time          : dead time, in MILLISECONDS
    # bias_voltage       : V_dc < V_br  /!\  (constant DC bias)
    # gate_voltage       : voltage added during the gate window
    # gate_on_duration   : duration (in ms) during which detection is enabled
    # gate_off_duration  : duration (in ms) during which detection is disabled
    # clock_period       : simulated internal clock period (in ms)
    
    def __init__(self, linked_bit, breakdown_voltage=7, dead_time=300,
                 bias_voltage=5, gate_voltage=5,
                 gate_off_duration=20, gate_on_duration=20, clock_period=10):

        # Geiger mode requires V_dc + V_gate STRICTLY above the breakdown voltage.
        if bias_voltage + gate_voltage <= breakdown_voltage:
            raise ValueError(
                "bias_voltage + gate_voltage doit etre > breakdown_voltage"
            )

        self.mode = "linear"
        self.bias_voltage = bias_voltage
        self.gate_voltage = gate_voltage
        self.breakdown_voltage = breakdown_voltage  # V_br (V)

        self.bit_received = False
        self.linked_bit = linked_bit

        self.dead_time = dead_time  # in ms

        self.gate_off_duration = gate_off_duration  # in ms
        self.gate_on_duration = gate_on_duration    # in ms

        self.voltage = self.bias_voltage  # instantaneous bias across the APD

        self.clock_period = clock_period  # in ms

        self.gate_open = False  # True while the detection window is open

        self.is_running = True
        self.photon_event = threading.Event()
        self.gate_timer = 0

        # If dead_time_elapsed >= dead_time -> ready to detect.
        # If dead_time_elapsed <  dead_time -> currently in dead time.
        self.dead_time_elapsed = self.dead_time

    # Create the clock, subscribe the per-tick callbacks and start it
    def start_clock(self):
        self.clk = clock.Clock(self.clock_period)
        self.clk.subscribe(self.update_gate)
        self.clk.subscribe(self.update_voltage)
        self.clk.subscribe(self.update_mode)
        self.clk.subscribe(self.update_dead_time)
        self.clk.start()

    # Switch between linear and geiger mode depending on the bias voltage
    def update_mode(self):
        self.mode = "geiger" if self.voltage > self.breakdown_voltage else "linear"

    # Gating window (everything in ms):
    #   timer in [0, gate_on_duration[                       -> detection enabled
    #   timer in [gate_on_duration, on + off[                -> detection disabled
    # then the timer wraps around and the cycle repeats.
    # Called once per tick (the timer advances by clock_period ms each tick).
    def update_gate(self):
        self.gate_timer += self.clock_period
        if self.gate_timer >= self.gate_on_duration + self.gate_off_duration:
            self.gate_timer = 0
        self.gate_open = self.gate_timer < self.gate_on_duration

    # Update the APD bias voltage depending on the gating window
    def update_voltage(self):
        if self.gate_open:
            self.voltage = self.bias_voltage + self.gate_voltage
        else:
            self.voltage = self.bias_voltage

    # While a dead time is in progress, advance the counter by clock_period ms
    # each tick. Once dead_time_elapsed reaches dead_time, the detector is
    # ready again.
    def update_dead_time(self):
        if self.dead_time_elapsed < self.dead_time:
            self.dead_time_elapsed += self.clock_period
            if self.dead_time_elapsed == self.dead_time:
                print(bcolors.OKGREEN + f"APD rearmed ({self.linked_bit})" + bcolors.ENDC)

    # Triggered externally when a photon reaches the detector
    def receive_photon(self):
        self.photon_event.set()

    # For now detection is automatic (provided we are in geiger mode and within
    # the detection window).

    # Blocking function (run it in its own thread).
    # For now detect_photon returns nothing; later it will return True when a
    # photon is correctly detected.
    def detect_photon(self):
        while self.is_running:
            self.photon_event.wait()   # wait for a photon
            self.photon_event.clear()  # lower the signal flag
            print(bcolors.OKBLUE + f"Photon received... ({self.linked_bit})!" + bcolors.ENDC)

            if not self.gate_open:
                print(bcolors.WARNING +
                      f"Gate is closed, photon was discarded ({self.linked_bit})!" + bcolors.ENDC)
            elif self.mode == "linear":
                print(bcolors.WARNING +
                      f"APD isn't in geiger mode, photon was discarded ({self.linked_bit})!" + bcolors.ENDC)
            elif self.dead_time_elapsed < self.dead_time:
                print(bcolors.WARNING +
                      f"APD is in a dead time, photon was discarded ({self.linked_bit})!" + bcolors.ENDC)
            else:
                print(bcolors.OKGREEN +
                      f"Photon correctly detected ({self.linked_bit})!" + bcolors.ENDC)
                self.dead_time_elapsed = 0  # start the dead time

    # Start the simulation: launches the (single) internal clock.
    def run(self):
        self.start_clock()
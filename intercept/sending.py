import qutip


# ████ █████ █   █ ████  ███ █   █  ███      ████ █████  ███  █████ ███  ███  █   █
#█     █     ██  █ █   █  █  ██  █ █        █     █     █       █    █  █   █ ██  █
# ███  ████  █ █ █ █   █  █  █ █ █ █  ██     ███  ████  █       █    █  █   █ █ █ █
#    █ █     █  ██ █   █  █  █  ██ █   █        █ █     █       █    █  █   █ █  ██
#████  █████ █   █ ████  ███ █   █  ███     ████  █████  ███    █   ███  ███  █   █

# Sending side of the interceptor: it re-emits qubits towards the receiver.
# Attributes used here (STATES, counters, quantum_channel...) are created by the
# factory (see intercept.factory).
class SendingMixin:

    def emit_qubit(self, bit : int):
        if self.sent_qubit_count == 0:
            self.communication_in_progress = True
        qubit = self.STATES[(bit, self.chosen_bases[len(self.chosen_bases)-1])]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        if self.sent_qubit_count == self.message_size:
            self.communication_in_progress = False
            self.communication_finished.set()   # unblock anyone waiting

    def send_qubit(self, qubit : qutip.Qobj):
        self.quantum_channel.send_qubit(qubit, True) # True bc is for qubits was sended to bob

    def read_value(self, value : int):
        self.emit_qubit(value)
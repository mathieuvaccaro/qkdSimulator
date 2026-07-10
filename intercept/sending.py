import qutip

class SendingMixin:

    def emit_qubit(self, bit : int):
        """Encode le bit dans la base courante d'Eve et l'émet vers Bob ; signale la fin lorsque tout le message a été envoyé

        Args:
            bit (int): bit à émettre
        """
        if self.sent_qubit_count == 0:
            self.communication_in_progress = True
        qubit = self.STATES[(bit, self.chosen_bases[len(self.chosen_bases)-1])]

        self.send_qubit(qubit)
        self.sent_qubit_count += 1

        if self.sent_qubit_count == self.message_size:
            self.communication_in_progress = False
            self.communication_finished.set()   # unblock anyone waiting

    def send_qubit(self, qubit : qutip.Qobj):
        """Émet le qubit d'Eve vers Bob sur le canal quantique

        Args:
            qubit (qutip.Qobj): qubit à émettre
        """
        self.quantum_channel.send_qubit(qubit, True) # True bc is for qubits was sended to bob

    def read_value(self, value : int):
        """Appelée par l'apd d'Eve : réémet immédiatement le bit mesuré vers Bob

        Args:
            value (int): bit mesuré à réémettre
        """
        self.emit_qubit(value)
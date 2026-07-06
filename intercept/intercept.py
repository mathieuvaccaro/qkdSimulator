# Entry point of the interceptor ("Eve").
#
# The interceptor is now split into three distinct parts:
#   - intercept.factory   : construction / shared state (the Intercept class)
#   - intercept.reception : reading (measuring) qubits from the sender
#   - intercept.sending   : re-emitting qubits towards the receiver
#
# An attack is a dedicated external file that subclasses Intercept and overrides
# receive_qubit / emit_qubit.
#
# This module is kept for backward compatibility: importing
# intercept.intercept.Intercept keeps working.
from intercept.factory import Intercept

__all__ = ["Intercept"]
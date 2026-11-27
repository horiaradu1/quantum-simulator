"""Compare gate sequences that should produce the same final state."""

import unittest

from numpy.testing import assert_allclose

from quantum_simulator import QuantumState


def _circuit_amplitudes(operations):
    state = QuantumState(4)
    state.initialize("0010")
    # The asymmetric complex amplitudes make swapping q0 and q3 observable.
    preparation = (("H", 0), ("CNOT", 0, 3), ("S", 3), ("H", 0), ("H", 1), ("T", 1))
    for gate, *wires in preparation + operations:
        state.apply_gate(gate, *wires)
    return state.amplitudes


class TestCircuitEquivalences(unittest.TestCase):
    """Check gate cancellation, substitution, and reordering."""

    def assert_circuits_match(self, operations, expected):
        assert_allclose(_circuit_amplitudes(operations), _circuit_amplitudes(expected), rtol=0, atol=1e-12)

    def test_phase_gate_powers(self):
        """T squared gives S and S squared gives Z."""
        for gate, squared_gate in (("T", "S"), ("S", "Z")):
            with self.subTest(gate=gate):
                self.assert_circuits_match(((gate, 1), (gate, 1)), ((squared_gate, 1),))

    def test_controlled_phase_gate_powers(self):
        """CT twice gives CS and CS twice gives CZ on reversed, nonadjacent wires."""
        for gate, squared_gate in (("CT", "CS"), ("CS", "CZ")):
            with self.subTest(gate=gate):
                self.assert_circuits_match(((gate, 3, 1), (gate, 3, 1)), ((squared_gate, 3, 1),))

    def test_hadamard_conjugation(self):
        """H, X, H gives Z."""
        self.assert_circuits_match((("H", 1), ("X", 1), ("H", 1)), (("Z", 1),))

    def test_hadamard_twice(self):
        """Two Hadamards restore the state."""
        state = QuantumState(3)
        state.initialize("110")
        initial_amplitudes = state.amplitudes

        state.apply_gate("H", 1)
        state.apply_gate("H", 1)

        assert_allclose(state.amplitudes, initial_amplitudes, atol=1e-12)

    def test_reverse_cnot(self):
        """Reverse CNOT matches CNOT with swapped wires."""
        self.assert_circuits_match((("CNOT10", 0, 3),), (("CNOT", 3, 0),))

    def test_swap_decomposition(self):
        """Three alternating CNOTs implement SWAP."""
        alternating_cnots = (("CNOT", 0, 3), ("CNOT", 3, 0), ("CNOT", 0, 3))
        self.assert_circuits_match(alternating_cnots, (("SWAP", 0, 3),))

    def test_disjoint_gates_commute(self):
        """Gates on disjoint wires commute."""
        hadamard = ("H", 1)
        cnot = ("CNOT", 0, 3)
        self.assert_circuits_match((hadamard, cnot), (cnot, hadamard))

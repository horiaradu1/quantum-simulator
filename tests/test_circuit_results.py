"""Check complete circuits against known complex amplitudes and probabilities."""

import unittest
from math import sqrt

import numpy as np
from numpy.testing import assert_allclose

from quantum_simulator import Outcome, QuantumState


class TestCircuitResults(unittest.TestCase):
    """Verify Bell-state output and a phase-sensitive four-qubit circuit."""

    def test_results_for_bell_state(self):
        """Bell-state results."""
        state = QuantumState(2)
        state.apply_gate("H", 0)
        state.apply_gate("CNOT", 0, 1)

        outcomes = list(state.outcomes())
        self.assertEqual([row.basis for row in outcomes], ["00", "01", "10", "11"])
        self.assertIsInstance(outcomes[0], Outcome)
        expected_amplitudes = np.array([1, 0, 0, 1]) / sqrt(2)
        assert_allclose([row.amplitude for row in outcomes], expected_amplitudes)
        assert_allclose([row.magnitude for row in outcomes], expected_amplitudes)
        assert_allclose([row.probability for row in outcomes], [0.5, 0, 0, 0.5])

    def test_results_for_four_qubit_circuit(self):
        """Four-qubit circuit results."""
        state = QuantumState(4)
        state.initialize("0110")
        operations = (
            ("H", 0),
            ("X", 2),
            ("S", 0),
            ("SWAP", 0, 1),
            ("CNOT", 1, 2),
            ("CNOT", 2, 3),
            ("H", 3),
            ("CNOT10", 2, 3),
            ("S", 3),
            ("CNOT10", 1, 2),
            ("CH", 2, 3),
            ("H", 2),
        )
        for gate, *wires in operations:
            state.apply_gate(gate, *wires)

        real_part = sqrt(1 / 8)
        expected_amplitudes = [0] * 8 + [
            real_part + 0.25j,
            0.25j,
            real_part - 0.25j,
            -0.25j,
            0.25j,
            real_part - 0.25j,
            -0.25j,
            real_part + 0.25j,
        ]
        expected_probabilities = [0] * 8 + [
            0.1875, 0.0625, 0.1875, 0.0625, 0.0625, 0.1875, 0.0625, 0.1875,
        ]
        assert_allclose(state.amplitudes, expected_amplitudes, atol=1e-12)
        assert_allclose(state.probabilities, expected_probabilities, atol=1e-12)

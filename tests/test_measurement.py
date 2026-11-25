"""Test sampling, measurement in two bases, and the state after measurement."""

import unittest
from math import sqrt

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from quantum_simulator import QuantumState

STATE_PREPARATION_GATE = [
    [0.6, -0.8],
    [0.8,  0.6],
]


class TestMeasurement(unittest.TestCase):
    """Check sampled frequencies and collapse on single- and multi-qubit registers."""

    def test_computational_basis(self):
        """Computational-basis measurement."""
        for bits in ("0", "1"):
            with self.subTest(basis=bits):
                state = QuantumState(1)
                state.initialize(bits)
                self.assertEqual(state.measure(), bits)

        state = QuantumState(1, rng=np.random.default_rng(2026))
        state.apply_gate(STATE_PREPARATION_GATE, 0)
        measured = state.measure()
        self.assertIn(measured, ("0", "1"))
        expected = [1, 0] if measured == "0" else [0, 1]
        assert_array_equal(state.amplitudes, expected)
        self.assertEqual(state.measure(), measured)

    def test_plus_minus_basis(self):
        """Measure in the ± basis using H."""
        for bits, sign in (("0", 1), ("1", -1)):
            with self.subTest(basis=bits):
                state = QuantumState(1, rng=np.random.default_rng(2026))
                state.initialize(bits)
                state.apply_gate("H", 0)
                expected = np.array([1, sign]) / sqrt(2)
                assert_allclose(state.amplitudes, expected)

                # H maps the +/- basis to 0/1 for the simulator's measurement.
                state.apply_gate("H", 0)
                self.assertEqual(state.measure(), bits)
                state.apply_gate("H", 0)
                assert_allclose(state.amplitudes, expected)

    def test_sampling(self):
        """Sampling preserves the state."""
        state = QuantumState(2, rng=np.random.default_rng(2026))
        state.apply_gate(STATE_PREPARATION_GATE, 1)
        state.apply_gate("S", 1)
        samples = [state.sample() for _ in range(4096)]

        self.assertEqual(set(samples), {"00", "01"})
        frequency_of_00 = samples.count("00") / len(samples)
        self.assertAlmostEqual(frequency_of_00, 0.6**2, delta=0.035)
        assert_allclose(state.amplitudes, [0.6, 0.8j, 0, 0])

    def test_sampling_then_measurement(self):
        """Five-qubit measurement collapse."""
        state = QuantumState(5, rng=np.random.default_rng(2026))
        state.initialize("01100")
        state.apply_gate("H", 0)
        state.apply_gate("X", 1)
        state.apply_gate("CNOT10", 0, 1)

        before_sampling = state.amplitudes
        possible_results = {"00100", "10100"}
        for _ in range(6):
            self.assertIn(state.sample(), possible_results)
        assert_array_equal(state.amplitudes, before_sampling)

        measured = state.measure()
        self.assertIn(measured, possible_results)
        expected = np.zeros(32)
        expected[int(measured, 2)] = 1
        assert_array_equal(state.amplitudes, expected)
        self.assertEqual(state.measure(), measured)
        self.assertEqual(state.sample(), measured)

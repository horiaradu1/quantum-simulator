"""Test computational basis initialization and the order of qubits in a register."""

import unittest

import numpy as np
from numpy.testing import assert_array_equal

from quantum_simulator import QuantumState


def basis_vector(bits):
    amplitudes = np.zeros(2**len(bits), dtype=complex)
    amplitudes[int(bits, 2)] = 1
    return amplitudes


class TestState(unittest.TestCase):
    """Check the register before and after setting its basis bits."""

    def test_new_register(self):
        """New registers start at zero."""
        state = QuantumState(5)
        assert_array_equal(state.amplitudes, basis_vector("00000"))

    def test_initialization_bit_order(self):
        """Initialization preserves bit order."""
        for bits in ("100", "001", "01100"):
            with self.subTest(bits=bits):
                state = QuantumState(len(bits))
                state.initialize([int(bit) for bit in bits])
                assert_array_equal(state.amplitudes, basis_vector(bits))
                self.assertEqual(state.sample(), bits)

    def test_reinitialization(self):
        """Reinitialization clears the previous state."""
        state = QuantumState(5)
        state.apply_gate("H", 0)
        state.initialize("00001")
        assert_array_equal(state.amplitudes, basis_vector("00001"))

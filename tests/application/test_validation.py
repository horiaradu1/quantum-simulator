"""Check how the simulator handles invalid inputs to its Python API."""

import unittest

from numpy.testing import assert_array_equal

from quantum_simulator import QuantumState


class TestInputValidation(unittest.TestCase):
    """Check that invalid register and gate inputs preserve the current state."""

    def test_reject_invalid_gates(self):
        """Invalid gates leave the state intact."""
        state = QuantumState(2)
        state.initialize("01")
        identity = [
            [1, 0],
            [0, 1],
        ]
        singular = [
            [0.5, 0.5],
            [0.5, 0.5],
        ]
        nonunitary = [
            [5, 4],
            [3, 7],
        ]
        cases = (
            ("missing", (0,)),
            ("H", ()),
            ("H", (-1,)),
            ("X", (2,)),
            ("CNOT", (0,)),
            ("CNOT", (0, 0)),
            (identity, (0, 1)),
            (singular, (0,)),
            (nonunitary, (0,)),
        )
        for gate, wires in cases:
            with self.subTest(gate=gate, wires=wires):
                with self.assertRaises(ValueError):
                    state.apply_gate(gate, *wires)
                assert_array_equal(state.amplitudes, [0, 1, 0, 0])

    def test_invalid_initialization(self):
        """Invalid qubit counts and bits."""
        for count in (0, -1, 2.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                QuantumState(count)

        state = QuantumState(2)
        state.initialize("01")
        for bits in ("0", "000", "0x", [0, 2], [0, 0.5]):
            with self.subTest(bits=bits):
                with self.assertRaises(ValueError):
                    state.initialize(bits)
                assert_array_equal(state.amplitudes, [0, 1, 0, 0])

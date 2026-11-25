"""Check individual gates against their matrices and basis-state truth tables."""

import unittest
from math import sqrt

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from quantum_simulator import QuantumState


class TestGates(unittest.TestCase):
    """Apply gates to basis states and superpositions, including on reordered wires."""

    def assert_gate_matrix(self, gate, qubit_count, matrix):
        # The columns give the gate's output for each basis input.
        for index, expected in enumerate(np.asarray(matrix).T):
            bits = format(index, f"0{qubit_count}b")
            with self.subTest(input=bits):
                state = QuantumState(qubit_count)
                state.initialize(bits)
                state.apply_gate(gate, *range(qubit_count))
                assert_allclose(state.amplitudes, expected, atol=1e-12)
                self.assertAlmostEqual(state.probabilities.sum(), 1)

    def assert_gate_permutation(self, gate, qubit_count, output_indices):
        matrix = np.eye(len(output_indices))[:, output_indices]
        self.assert_gate_matrix(gate, qubit_count, matrix)

    def test_1_qubit_h(self):
        """H gate."""
        matrix = np.array([
            [1,  1],
            [1, -1],
        ]) / sqrt(2)
        self.assert_gate_matrix("H", 1, matrix)

    def test_1_qubit_s(self):
        """S gate."""
        self.assert_gate_matrix("S", 1, [
            [1,  0],
            [0, 1j],
        ])

    def test_1_qubit_t(self):
        """T gate."""
        self.assert_gate_matrix("T", 1, [
            [1, 0],
            [0, (1 + 1j) / sqrt(2)],
        ])

    def test_1_qubit_x(self):
        """X gate."""
        self.assert_gate_matrix("X", 1, [
            [0, 1],
            [1, 0],
        ])

    def test_1_qubit_y(self):
        """Y gate."""
        self.assert_gate_matrix("Y", 1, [
            [ 0, -1j],
            [1j,   0],
        ])

    def test_1_qubit_z(self):
        """Z gate."""
        self.assert_gate_matrix("Z", 1, [
            [1,  0],
            [0, -1],
        ])

    def test_1_qubit_x_and_y_on_superposition(self):
        """X and Y on a superposition."""
        # The first column prepares amplitudes [0.6, 0.8] from |0>.
        preparation = [
            [0.6, -0.8],
            [0.8,  0.6],
        ]
        for gate, expected in (("X", [0.8, 0.6]), ("Y", [-0.8j, 0.6j])):
            with self.subTest(gate=gate):
                state = QuantumState(1)
                state.apply_gate(preparation, 0)
                state.apply_gate(gate, 0)
                assert_allclose(state.amplitudes, expected)

    def test_2_qubit_ch(self):
        """Controlled-H gate."""
        matrix = [
            [1, 0,           0,            0],
            [0, 1,           0,            0],
            [0, 0, 1 / sqrt(2),  1 / sqrt(2)],
            [0, 0, 1 / sqrt(2), -1 / sqrt(2)],
        ]
        self.assert_gate_matrix("CH", 2, matrix)

    def test_2_qubit_cnot(self):
        """CNOT truth table."""
        self.assert_gate_permutation("CNOT", 2, (0, 1, 3, 2))

    def test_2_qubit_cnot10(self):
        """Reverse CNOT truth table."""
        self.assert_gate_permutation("CNOT10", 2, (0, 3, 2, 1))

    def test_2_qubit_swap(self):
        """SWAP truth table."""
        self.assert_gate_permutation("SWAP", 2, (0, 2, 1, 3))

    def test_3_qubit_toffoli(self):
        """Toffoli truth table."""
        self.assert_gate_permutation("TOFFOLI", 3, (0, 1, 2, 3, 4, 5, 7, 6))

    def test_wire_order(self):
        """Reversed and nonadjacent wires."""
        cases = (
            ("CNOT", (3, 0), "0001", "1001"),
            ("CNOT", (3, 0), "1000", "1000"),
            ("CNOT10", (0, 2), "0010", "1010"),
            ("SWAP", (2, 0), "0011", "1001"),
            ("TOFFOLI", (3, 0, 2), "1101", "1111"),
            ("TOFFOLI", (3, 0, 2), "1100", "1100"),
            ("TOFFOLI", (3, 0, 2), "0101", "0101"),
        )
        for gate, wires, input_bits, output_bits in cases:
            with self.subTest(gate=gate, wires=wires, input=input_bits):
                state = QuantumState(4)
                state.initialize(input_bits)
                state.apply_gate(gate, *wires)

                expected = np.zeros(16)
                expected[int(output_bits, 2)] = 1
                assert_array_equal(state.amplitudes, expected)

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

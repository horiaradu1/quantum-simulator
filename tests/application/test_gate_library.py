"""Define gates from matrices and check how they are validated and applied, without Qt."""

import unittest
from math import sqrt

import numpy as np
from numpy.testing import assert_allclose

from quantum_simulator import Circuit, PlacedGate, QuantumState, run
from quantum_simulator.backend.expressions import parse_complex
from quantum_simulator.backend.gate_library import GateLibrary, MatrixGate


def _hadamard(entry):
    return [
        [entry,  entry],
        [entry, -entry],
    ]


class TestMatrixGates(unittest.TestCase):
    """Check which matrices become gates and that a named matrix acts like the matrix itself."""

    def test_rounded_unitaries_are_accepted_and_others_rejected(self):
        """Rounded unitaries become exact unitaries; wrong sizes, non-finite, nonunitary and taken names fail."""
        # The lab's 8-digit H and the 4 digits shown in the results table are within the tolerance.
        for entry in (0.70710678, 0.7071):
            with self.subTest(entry=entry):
                matrix = MatrixGate("H2", _hadamard(entry)).matrix
                assert_allclose(matrix.conj().T @ matrix, np.eye(2), rtol=0, atol=1e-12)

        library = GateLibrary([MatrixGate("Rot", np.eye(2))])
        rejected = {
            "3 digits": lambda: MatrixGate("H3", _hadamard(0.707)),
            "diag(1, 1.001)": lambda: MatrixGate("Near", [[1, 0], [0, 1.001]]),
            "3x3 matrix": lambda: MatrixGate("Odd", np.eye(3)),
            "NaN entry": lambda: MatrixGate("Nan", [[np.nan, 0], [0, 1]]),
            "infinite entry": lambda: MatrixGate("Inf", [[np.inf, 0], [0, 1]]),
            # U†U overflows, and the NaN error once passed every tolerance check.
            "huge entry": lambda: MatrixGate("Huge", [[1e200 + 1e200j, 0], [0, 1]]),
            "built-in name": lambda: library.check(MatrixGate("cy", np.eye(4))),
            "name of another gate": lambda: library.check(MatrixGate("ROT", [[0, 1], [1, 0]])),
        }
        for case, define in rejected.items():
            with self.subTest(case=case), self.assertRaises(ValueError):
                define()

    def test_cells_accept_numbers_and_simple_expressions(self):
        """Matrix cells accept complex numbers, powers, sqrt, exp, pi, e and i, and nothing else."""
        values = {
            "0.5-0.5i": 0.5 - 0.5j,
            "-i": -1j,
            "1/sqrt(2)": 1 / sqrt(2),
            "exp(i*pi/4)": (1 + 1j) / sqrt(2),
            "e^(i*pi)": -1,
            # ^ is a power, so it binds tighter than minus and times.
            "-1^2": -1,
            "2*3^2": 18,
            # A negative zero from -1 would put this on the other side of the branch cut, giving -i.
            "sqrt(-1)": 1j,
            "cos(pi)": -1,
            "-i*sin(pi/2)": -1j,
        }
        for text, expected in values.items():
            with self.subTest(text=text):
                self.assertAlmostEqual(parse_complex(text), expected)
        for text in ("", "abc", "1/0", "__import__('os')"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_complex(text)

    def test_two_wire_matrix_gate_on_reversed_wires(self):
        """A named two-wire matrix on q3 and q0 matches applying the matrix to those wires directly."""
        # CY written out, so swapping its wires changes the result.
        matrix = [
            [1, 0,  0,   0],
            [0, 1,  0,   0],
            [0, 0,  0, -1j],
            [0, 0, 1j,   0],
        ]
        gates = (PlacedGate(0, "H", (3,)), PlacedGate(1, "U2", (3, 0)))
        circuit = Circuit(4, "0010", gates, definitions=(MatrixGate("U2", matrix),))

        expected = QuantumState(4)
        expected.initialize("0010")
        expected.apply_gate("H", 3)
        expected.apply_gate(matrix, 3, 0)
        assert_allclose(run(circuit).amplitudes, expected.amplitudes, atol=1e-12)

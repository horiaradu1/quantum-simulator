"""Check mathematical properties of the built-in gate matrices."""

import unittest

import numpy as np
from numpy.testing import assert_allclose

from quantum_simulator.backend.gates import _GATES


class TestGateProperties(unittest.TestCase):
    """Compare each gate with its conjugate transpose and test unitarity."""

    def test_all_builtin_gates_are_unitary(self):
        """Every built-in gate is unitary."""
        for gate, matrix in _GATES.items():
            with self.subTest(gate=gate):
                rows, columns = matrix.shape
                self.assertEqual(rows, columns)
                adjoint = matrix.conj().T
                assert_allclose(adjoint @ matrix, np.eye(rows), rtol=0, atol=1e-12)

    def test_builtin_gate_hermiticity(self):
        """All built-in gates except S, T, CS and CT are Hermitian."""
        hermitian_gates = ("H", "X", "Y", "Z", "CNOT", "CNOT10", "CH", "CY", "CZ", "SWAP", "TOFFOLI")
        phase_gates = ("S", "T", "CS", "CT")
        for expected, gates in ((True, hermitian_gates), (False, phase_gates)):
            for gate in gates:
                with self.subTest(gate=gate):
                    matrix = _GATES[gate]
                    is_hermitian = np.allclose(matrix, matrix.conj().T, rtol=0, atol=1e-12)
                    self.assertEqual(is_hermitian, expected)

"""Check gates from circuits and controlled gates on chosen wires against known states and gate-by-gate runs."""

import unittest
from math import sqrt

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from quantum_simulator import (
    Circuit,
    CircuitGate,
    ControlledGate,
    GateOperation,
    MatrixGate,
    PlacedGate,
    QuantumState,
    run,
)
from quantum_simulator.backend.gate_library import GateLibrary
from quantum_simulator.backend.gates import controlled, gate_matrix

BELL = CircuitGate("Bell", 2, (GateOperation("H", (0,)), GateOperation("CNOT", (0, 1))))


class TestCircuitGates(unittest.TestCase):
    """Run gates from circuits and Controlled-U on separated, reordered wires."""

    def test_bell_circuit_gate_on_separated_wires(self):
        """A Bell gate from a circuit on q3 and q1 gives 1/√2 at 0000 and 0101 and nothing else."""
        circuit = Circuit(4, "0000", (PlacedGate(0, "Bell", (3, 1)),), definitions=(BELL,))

        expected = np.zeros(16)
        expected[0b0000] = expected[0b0101] = 1 / sqrt(2)
        assert_allclose(run(circuit).amplitudes, expected, atol=1e-12)

    def test_controlled_nested_circuit_gate_matches_controlled_operations(self):
        """Controlling a nested gate from a circuit equals controlling each of its operations, with the control in superposition."""
        quarter_turn = MatrixGate("QTurn", [[1, 0], [0, 1j]])
        inner = CircuitGate("Inner", 2, (GateOperation("QTurn", (1,)), GateOperation("CNOT", (1, 0))))
        outer = CircuitGate(
            "Outer", 3, (GateOperation("H", (0,)), GateOperation("Inner", (2, 0)), GateOperation("CY", (1, 2)))
        )
        controlled_outer = ControlledGate("COuter", "Outer", 4)
        # The control q4 is in superposition. Outer's local wires 0, 1 and 2 go to q0, q3 and q1.
        gates = (PlacedGate(0, "H", (4,)), PlacedGate(0, "H", (3,)), PlacedGate(1, "COuter", (4, 0, 3, 1)))
        definitions = (quarter_turn, inner, outer, controlled_outer)
        circuit = Circuit(5, "01000", gates, definitions=definitions)

        # The same operations mapped to the register, each with q4 as one extra control.
        expected = QuantumState(5)
        expected.initialize("01000")
        expected.apply_gate("H", 4)
        expected.apply_gate("H", 3)
        expected.apply_gate(controlled(gate_matrix("H", 1)), 4, 0)
        expected.apply_gate(controlled(quarter_turn.matrix), 4, 0)
        expected.apply_gate(controlled(gate_matrix("CNOT", 2)), 4, 0, 1)
        expected.apply_gate(controlled(gate_matrix("CY", 2)), 4, 3, 1)
        assert_allclose(run(circuit).amplitudes, expected.amplitudes, atol=1e-12)

    def test_controlled_cnot_is_toffoli(self):
        """One control added before CNOT gives Toffoli's matrix, with both controls before the target."""
        library = GateLibrary([ControlledGate("CCNOT", "CNOT", 3)])
        assert_array_equal(library.matrix("CCNOT"), library.matrix("TOFFOLI"))

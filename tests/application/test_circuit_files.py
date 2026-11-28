"""Save, reopen and validate circuit files without Qt."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from quantum_simulator import Circuit, CircuitGate, GateOperation, PlacedGate, RunSettings, run
from quantum_simulator.backend.circuit_file import load_circuit, save_circuit, shared_circuits
from quantum_simulator.backend.editor import EditorSession
from quantum_simulator.backend.gate_file import export_gates, load_gates
from quantum_simulator.backend.gate_library import ControlledGate, GateLibrary, MatrixGate


class TestCircuitFiles(unittest.TestCase):
    """Write circuits and gate libraries to a temporary folder and read them back."""

    def test_saved_circuit_reopens_unchanged(self):
        """A circuit with nested custom gates reopens in a fresh session with the same columns, gates, settings and amplitudes."""
        # A 4-digit rotation is stored as its nearest unitary, which must survive the round trip.
        rotation = MatrixGate("Rot", [[0.7071, -0.7071], [0.7071, 0.7071]])
        pair = CircuitGate("Pair", 2, (GateOperation("Rot", (1,)), GateOperation("CNOT", (1, 0))))
        definitions = (rotation, ControlledGate("CRot", "Rot", 2), pair, ControlledGate("CPair", "Pair", 3))
        # Nonzero initial bits, an empty column, reversed wires, a controlled gate from a circuit and a trailing empty column.
        gates = (
            PlacedGate(0, "H", (0,)),
            PlacedGate(2, "CNOT", (2, 0)),
            PlacedGate(3, "CRot", (2, 1)),
            PlacedGate(4, "CPair", (0, 2, 1)),
        )
        circuit = Circuit(3, "101", gates, column_count=6, definitions=definitions)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            for settings in (RunSettings(seed=5), None):
                with self.subTest(settings=settings):
                    save_circuit(path, circuit, settings)
                    reopened, reopened_settings = load_circuit(path)

                    self.assertEqual(reopened, circuit)
                    self.assertEqual(reopened_settings, settings)
                    assert_array_equal(run(reopened, reopened_settings).amplitudes, run(circuit).amplitudes)

                    # A new session starts with no custom gates, so everything must come from the file.
                    session = EditorSession(qubits=1)
                    session.load(reopened, reopened_settings)
                    self.assertEqual(session.circuit(reopened.initial_bits), circuit)

    def test_exported_gate_imports_into_empty_library(self):
        """An exported gate carries each custom gate it needs once, and acts the same on every basis input."""
        quarter_turn = MatrixGate("QTurn", [[1, 0], [0, 1j]])
        inner = CircuitGate("Inner", 2, (GateOperation("QTurn", (1,)), GateOperation("H", (0,))))
        outer = CircuitGate("Outer", 3, (GateOperation("Inner", (2, 0)), GateOperation("Inner", (0, 1))))
        unused = MatrixGate("Unused", np.eye(2))
        library = GateLibrary([quarter_turn, inner, outer, ControlledGate("COuter", "Outer", 4), unused])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "COuter.json"
            export_gates(path, library, ["COuter"])
            definitions = load_gates(path)
        self.assertEqual([definition.gate_id for definition in definitions], ["QTurn", "Inner", "Outer", "COuter"])

        session = EditorSession(qubits=4)
        session.import_gates(definitions)
        # Column j of a gate's matrix is the state it makes from basis input j.
        assert_allclose(session.library.matrix("COuter"), library.matrix("COuter"), atol=1e-12)

    def test_circuits_a_file_would_reject_cannot_be_built(self):
        """Every rule checked when opening a file is checked when building a circuit, so it cannot be saved."""
        invalid = {
            "unknown gate": lambda: Circuit(1, "0", (PlacedGate(0, "FOO", (0,)),)),
            "CNOT on one wire": lambda: Circuit(2, "00", (PlacedGate(0, "CNOT", (0,)),)),
            "bad initial bits": lambda: Circuit(2, "2x"),
            "too many qubits": lambda: Circuit(40, "0" * 40),
            "undefined base gate": lambda: Circuit(2, "00", definitions=(ControlledGate("CFoo", "Foo", 2),)),
        }
        for case, build in invalid.items():
            with self.subTest(case=case), self.assertRaises(ValueError):
                build()

    def test_shared_bell_circuit_still_opens(self):
        """The shared Bell circuit opens in the current format and gives 50% for 00 and 11."""
        circuit, settings = load_circuit(shared_circuits()["bell"])
        assert_allclose(run(circuit, settings).probabilities, [0.5, 0, 0, 0.5])

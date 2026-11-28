"""Save, reopen and validate circuit files without Qt."""

import tempfile
import unittest
from pathlib import Path

from numpy.testing import assert_allclose, assert_array_equal

from quantum_simulator import Circuit, PlacedGate, RunSettings, run
from quantum_simulator.backend.circuit_file import load_circuit, save_circuit, shared_circuits
from quantum_simulator.backend.gate_library import ControlledGate, MatrixGate

class TestCircuitFiles(unittest.TestCase):
    """Write circuits to a temporary folder and read circuit files back."""

    def test_saved_circuit_reopens_unchanged(self):
        """A saved circuit reopens with the same columns, user gates, settings and amplitudes."""
        # A 4-digit rotation is stored as its nearest unitary, which must survive the round trip.
        rotation = MatrixGate("Rot", [[0.7071, -0.7071], [0.7071, 0.7071]])
        definitions = (rotation, ControlledGate("CRot", "Rot", 2))
        # Nonzero initial bits, an empty column, reversed wires and a trailing empty column.
        gates = (PlacedGate(0, "H", (0,)), PlacedGate(2, "CNOT", (2, 0)), PlacedGate(3, "CRot", (2, 1)))
        circuit = Circuit(3, "101", gates, column_count=5, definitions=definitions)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            for settings in (RunSettings(seed=5), None):
                with self.subTest(settings=settings):
                    save_circuit(path, circuit, settings)
                    reopened, reopened_settings = load_circuit(path)

                    self.assertEqual(reopened, circuit)
                    self.assertEqual(reopened_settings, settings)
                    assert_array_equal(run(reopened, reopened_settings).amplitudes, run(circuit).amplitudes)

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

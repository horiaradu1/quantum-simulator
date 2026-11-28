"""Check the editor session's rules for changing a circuit, without Qt."""

import unittest

from quantum_simulator.backend.circuit import PlacedGate
from quantum_simulator.backend.editor import EditorSession, Placement
from quantum_simulator.backend.gate_library import ControlledGate, MatrixGate


def _run(session, initial_bits):
    for _ in session.run_steps(initial_bits):
        pass


class TestEditorSession(unittest.TestCase):
    """Edit a circuit through the session and check its gates and last result."""

    def test_obsolete_runs_cannot_publish_results(self):
        """Editing or starting a newer run cancels an iterator even before its first step."""
        session = EditorSession(qubits=1)
        session.select_gate("X")
        session.place(0, 0)
        active = session.run_steps("0")
        next(active)
        session.clear()
        self.assertEqual(list(active), [])
        self.assertIsNone(session.result)

        session.place(0, 0)
        unstarted = session.run_steps("0")
        older = session.run_steps("0")
        next(older)
        _run(session, "1")
        latest = session.result
        self.assertEqual(latest.sample(), "0")
        self.assertEqual(list(unstarted), [])
        self.assertEqual(list(older), [])
        self.assertIs(session.result, latest)

    def test_invalid_cell_preserves_pending_control(self):
        """An invalid cell leaves a pending CNOT ready for its original target."""
        session = EditorSession(qubits=2)
        session.select_gate("CNOT")
        self.assertIs(session.place(0, 0), Placement.WAITING)
        for step, wire in ((1, 2), (1, -1), (1, True), (-1, 1), (0.5, 1)):
            with self.subTest(step=step, wire=wire), self.assertRaises(ValueError):
                session.place(step, wire)
        self.assertIs(session.place(0, 1), Placement.PLACED)
        self.assertEqual(session.gates, [PlacedGate(0, "CNOT", (0, 1))])

    def test_edits_discard_last_result(self):
        """Placing, removing or clearing gates discards the last run's result."""
        session = EditorSession(qubits=2)
        session.place(0, 0)
        for edit in ("place", "remove", "clear"):
            with self.subTest(edit=edit):
                _run(session, "00")
                self.assertIsNotNone(session.result)

                if edit == "place":
                    session.place(1, 1)
                elif edit == "remove":
                    session.remove_at(1, 1)
                else:
                    session.clear()
                self.assertIsNone(session.result)

    def test_fewer_qubits_remove_gates_on_missing_wires(self):
        """Lowering the qubit count removes gates on missing wires and reselects H if needed."""
        session = EditorSession(qubits=3)
        session.place(0, 0)
        session.select_gate("TOFFOLI")
        for wire in (0, 1, 2):
            session.place(1, wire)

        session.set_qubit_count(2)

        self.assertEqual(session.gates, [PlacedGate(0, "H", (0,))])
        self.assertEqual(session.selected_gate, "H")

    def test_gates_in_use_cannot_be_deleted(self):
        """A custom gate can be deleted only when no placed gate or other custom gate uses it."""
        session = EditorSession(qubits=2)
        rotation = MatrixGate("Rot", [[0.6, -0.8], [0.8, 0.6]])
        session.library.add(rotation, ControlledGate("CRot", "Rot", 2))
        session.select_gate("CRot")
        session.place(0, 0)
        session.place(0, 1)

        # H is built in, CRot is placed, and CRot is built from Rot.
        for gate_id in ("H", "CRot", "Rot"):
            with self.subTest(gate=gate_id), self.assertRaises(ValueError):
                session.delete_gate(gate_id)

        session.remove_at(0, 0)
        session.delete_gate("CRot")
        session.delete_gate("Rot")
        self.assertEqual(session.library.user_definitions, ())

"""Exercise gate placement, the desktop Run workflow, and cleanup after simulation."""

import gc
import os
import tempfile
import unittest
import weakref
from pathlib import Path
from unittest.mock import patch

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal
from PySide6.QtCore import QEvent, QMimeData, QPointF, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFileDialog, QInputDialog, QMessageBox

from quantum_simulator.backend import Circuit, ControlledGate, MatrixGate, PlacedGate, QuantumState, run
from quantum_simulator.backend.circuit_file import save_circuit
from quantum_simulator.backend.gate_file import load_gates, save_gates
from quantum_simulator.backend.gate_library import CircuitGate, ClashChoice, GateOperation
from quantum_simulator.gui.gate_button import GATE_MIME_TYPE
from quantum_simulator.gui.gate_dialogs import CircuitGateDialog, ControlledGateDialog, MatrixGateDialog
from quantum_simulator.gui.gate_manager import GateManagerDialog
from quantum_simulator.gui.window import SimulatorWindow

TEST_CIRCUITS = Path(__file__).parents[1] / "resources" / "circuits"


class WindowTestCase(unittest.TestCase):
    """Open an offscreen simulator window for each test."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Answer "Don't save" to any question, so a prompt never blocks an offscreen test.
        # Tests about prompts patch the answer themselves.
        answer_discard = patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard)
        answer_discard.start()
        self.addCleanup(answer_discard.stop)

        # Saved circuits and custom gates go to a temporary folder, never to the repository's data folder.
        data_directory = tempfile.TemporaryDirectory()
        self.addCleanup(data_directory.cleanup)
        self.data_directory = Path(data_directory.name)
        self.window = SimulatorWindow(self.data_directory)
        self.window.show()
        self.addCleanup(self.dispose_window)

    def dispose_window(self):
        if self.window is not None:
            self.window.close()
            self.window.deleteLater()
            self.app.sendPostedEvents(self.window, QEvent.Type.DeferredDelete)
            self.window = None

    def wait_for_editor(self):
        switched = QSignalSpy(self.window.pages.currentChanged)
        self.assertTrue(switched.wait(5000))
        self.assertFalse(self.window.loading_screen.isVisible())

    def drop_gate(self, gate_id, step, wire):
        # Send the events a palette drag delivers, so the canvas's own drop handlers run.
        view = self.window.circuit_view
        mime = QMimeData()
        mime.setData(GATE_MIME_TYPE, gate_id.encode("utf-8"))
        position = QPointF(view.mapFromScene(view.cell_center(step, wire)))
        drag = (Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(view.viewport(), QDragEnterEvent(position, *drag))
        drop = QDropEvent(position, *drag)
        QApplication.sendEvent(view.viewport(), drop)
        self.assertTrue(drop.isAccepted())

    def right_click_cell(self, step, wire):
        view = self.window.circuit_view
        position = view.mapFromScene(view.cell_center(step, wire))
        QTest.mouseClick(view.viewport(), Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, position)

    def create_gate(self, dialog_class, action, name, save_to=None):
        """Name a gate in a creation dialog, then press Create, or Create and save… choosing save_to."""
        def fill_and_choose(dialog):
            dialog.name_edit.setText(name)
            if save_to is None:
                return QDialog.DialogCode.Accepted.value
            with patch.object(QFileDialog, "getSaveFileName", return_value=(str(save_to), "")):
                dialog.save_button.click()
            return dialog.result()

        # Replacing exec with a plain function makes it receive the real dialog the window opens.
        with patch.object(dialog_class, "exec", fill_and_choose):
            action.trigger()


class TestGatePlacement(WindowTestCase):
    """Check how wire selections become complete gates in the editor."""

    def test_drag_bell_pair_after_removing_a_gate(self):
        """Dragging H and CNOT after right-clicking away a stray X gives the Python Bell state."""
        window = self.window
        self.drop_gate("X", 0, 1)
        self.right_click_cell(0, 1)
        self.drop_gate("H", 0, 0)
        self.drop_gate("CNOT", 1, 0)
        self.drop_gate("CNOT", 1, 1)
        window.run_button.click()
        self.wait_for_editor()

        table = window.results_table
        rows = [(table.item(row, 0).text(), table.item(row, 1).text()) for row in range(table.rowCount())]
        self.assertEqual(rows, [("00", "0.7071"), ("11", "0.7071")])

        bell = Circuit(2, "00", (PlacedGate(0, "H", (0,)), PlacedGate(1, "CNOT", (0, 1))))
        assert_array_equal(window.session.result.amplitudes, run(bell).amplitudes)

    def test_drag_cy_onto_reversed_nonadjacent_wires(self):
        """Dragging CY from q3 to q0 turns 0001 into +i on 1001. From q0 to q3, 0001 is unchanged."""
        window = self.window
        window.qubit_count.setValue(4)
        cases = (
            ((3, 0), "1001", "0.0000+1.0000i"),
            ((0, 3), "0001", "1.0000"),
        )
        for wires, basis, amplitude in cases:
            with self.subTest(wires=wires):
                window.clear_button.click()
                window.initial_state.setValue(0b0001)
                for wire in wires:
                    self.drop_gate("CY", 0, wire)
                window.run_button.click()
                self.wait_for_editor()

                table = window.results_table
                self.assertEqual(table.rowCount(), 1)
                self.assertEqual(table.item(0, 0).text(), basis)
                self.assertEqual(table.item(0, 1).text(), amplitude)

    def test_retry_cnot_target(self):
        """A CNOT keeps its control after a duplicate or blocked target."""
        window = self.window
        grid = window.circuit_view
        window.qubit_count.setValue(4)
        window.initial_state.setValue(0b1000)
        grid.gate_dropped.emit("X", 0, 2)
        grid.gate_dropped.emit("CNOT", 0, 0)

        grid.cell_clicked.emit(0, 0)
        self.assertIn("different wire", window.circuit_hint.text())
        grid.cell_clicked.emit(0, 3)
        self.assertIn("already crosses", window.circuit_hint.text())
        grid.cell_clicked.emit(0, 1)

        window.run_button.click()
        self.wait_for_editor()
        self.assertEqual(window.results_table.item(0, 0).text(), "1110")

    def test_restart_toffoli_in_another_step(self):
        """Choosing a new column restarts Toffoli at its first control."""
        window = self.window
        grid = window.circuit_view
        window.qubit_count.setValue(3)
        window.initial_state.setValue(0b011)
        grid.gate_dropped.emit("TOFFOLI", 0, 0)
        grid.cell_clicked.emit(0, 2)
        self.assertEqual(window.circuit_hint.text(), "Choose the target.")

        grid.cell_clicked.emit(1, 1)
        self.assertEqual(window.circuit_hint.text(), "Choose the second control.")
        grid.cell_clicked.emit(1, 2)
        grid.cell_clicked.emit(1, 0)

        window.run_button.click()
        self.wait_for_editor()
        self.assertEqual(window.results_table.item(0, 0).text(), "111")


class TestCircuitFiles(WindowTestCase):
    """Save and open circuits through the File menu."""

    def test_save_new_open_and_run(self):
        """A saved circuit reopens after New circuit and runs the same, with its name in the heading. An invalid file leaves it open."""
        window = self.window
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        window.saved_circuits = Path(directory.name)

        window.qubit_count.setValue(3)
        window.initial_state.setValue(0b101)
        self.drop_gate("H", 0, 0)
        self.drop_gate("CNOT", 2, 2)
        self.drop_gate("CNOT", 2, 0)
        expected = run(window.session.circuit("101")).amplitudes
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(window.saved_circuits / "demo.json"), "")):
            window.save_action.trigger()

        self.assertEqual(window.circuit_title.text(), "Circuit: demo")

        window.new_circuit_action.trigger()
        self.assertEqual(window.circuit_title.text(), "Circuit: Untitled")
        self.assertEqual(window.session.gates, [])
        window.qubit_count.setValue(2)
        saved_file = str(window.saved_circuits / "demo.json")
        with patch.object(QFileDialog, "getOpenFileName", return_value=(saved_file, "")):
            window.open_action.trigger()
        self.assertEqual(window.circuit_title.text(), "Circuit: demo")
        self.assertEqual(window.initial_state.text(), "101")
        window.run_button.click()
        self.wait_for_editor()
        assert_array_equal(window.session.result.amplitudes, expected)

        opened_gates = list(window.session.gates)
        invalid_file = str(TEST_CIRCUITS / "overlapping_gates.json")
        with (
            patch.object(QFileDialog, "getOpenFileName", return_value=(invalid_file, "")),
            patch.object(QMessageBox, "warning") as warning,
        ):
            window.open_action.trigger()
        warning.assert_called_once()
        self.assertIn("cross the same wires", warning.call_args.args[2])
        self.assertEqual(window.session.gates, opened_gates)

    def test_opened_circuit_shows_trailing_empty_columns(self):
        """An opened circuit shows all 30 of its empty columns, so a gate can be dropped in the last one."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "wide.json"
        save_circuit(path, Circuit(1, "0", column_count=30))

        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(path), "")):
            self.window.open_action.trigger()
        self.drop_gate("X", 29, 0)
        self.assertEqual(self.window.session.gates, [PlacedGate(29, "X", (0,))])


class TestUserGates(WindowTestCase):
    """Define gates through the Gates menu and use them in the circuit."""

    def test_define_open_edit_and_save_gate(self):
        """A saved gate from a circuit opens for editing and saves back to its own file, and an older circuit can use mine."""
        window = self.window
        window.qubit_count.setValue(1)
        self.drop_gate("H", 0, 0)
        # Outside the default gates folder, so saving must remember where the gate came from.
        gate_file = self.data_directory / "shared" / "Inner.json"
        self.create_gate(CircuitGateDialog, window.define_circuit_gate_action, "Inner", save_to=gate_file)
        self.assertTrue(gate_file.exists())

        window.new_circuit_action.trigger()
        window.qubit_count.setValue(2)
        self.drop_gate("Inner", 0, 0)
        self.drop_gate("Inner", 0, 1)
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(window.saved_circuits / "test.json"), "")):
            window.save_button.click()

        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(gate_file), "")):
            window.open_gate_action.trigger()
        self.assertEqual(window.circuit_title.text(), "Gate: Inner")
        self.assertFalse(window.qubit_count.isEnabled())
        # Placing Inner inside itself would make a cycle.
        self.assertFalse(window.gate_buttons["Inner"].isEnabled())

        self.right_click_cell(0, 0)
        self.drop_gate("X", 0, 0)
        # A failed write keeps the edits pending, so the user can save again.
        with (
            patch.object(Path, "replace", side_effect=OSError("disk full")),
            patch.object(QMessageBox, "warning") as warning,
        ):
            window.save_button.click()
        warning.assert_called_once()
        self.assertTrue(window.session.modified)
        self.assertEqual(window.session.library.circuit_gate("Inner").operations, (GateOperation("H", (0,)),))

        window.save_button.click()
        self.assertEqual(window.circuit_title.text(), "Gate: Inner")
        self.assertFalse(window.session.modified)
        self.assertEqual(load_gates(gate_file)[0].operations, (GateOperation("X", (0,)),))

        copy = self.data_directory / "copy.json"
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(copy), "")):
            window.save_as_action.trigger()
        self.drop_gate("Z", 1, 0)
        window.save_button.click()
        self.assertEqual(len(load_gates(copy)[0].operations), 2)
        self.assertEqual(len(load_gates(gate_file)[0].operations), 1)

        # test.json still holds the old Inner. Using mine runs the edited gate on both wires.
        test_file = str(window.saved_circuits / "test.json")
        with (
            patch.object(QFileDialog, "getOpenFileName", return_value=(test_file, "")),
            patch.object(SimulatorWindow, "_resolve_name_clash", return_value=ClashChoice.USE_LOCAL),
        ):
            window.open_action.trigger()
        self.assertEqual(window.circuit_title.text(), "Circuit: test")
        self.assertTrue(window.session.modified)
        assert_array_equal(run(window.session.circuit("00")).amplitudes, [0, 0, 0, 1])

    def test_define_matrix_gate_place_and_run(self):
        """A typed matrix becomes a palette gate that runs like its matrix. A nonunitary one cannot be added."""
        window = self.window

        def fill_cells(dialog, rows):
            for cells, texts in zip(dialog.cells, rows):
                for cell, text in zip(cells, texts):
                    cell.setText(text)

        def fill_and_accept(dialog):
            ok_button = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
            dialog.name_edit.setText("Rot")
            fill_cells(dialog, [["1", "0"], ["0", "1.001"]])
            self.assertFalse(ok_button.isEnabled())
            self.assertIn("not unitary", dialog.checks.details["Unitary"].text())

            # An expression shows its value under the cell.
            fill_cells(dialog, [["1", "0"], ["0", "exp(i*pi)"]])
            self.assertEqual(dialog.cell_values[1][1].text(), "= -1")
            self.assertTrue(dialog.cells[1][1].font().bold())
            dialog.cells[1][1].setText("1-1")
            self.assertFalse(dialog.cells[1][1].font().bold())

            fill_cells(dialog, [["0.6", "-0.8"], ["0.8", "0.6"]])
            self.assertTrue(ok_button.isEnabled())
            return QDialog.DialogCode.Accepted.value

        # Replacing exec with a plain function makes it receive the real dialog the window opens.
        with patch.object(MatrixGateDialog, "exec", fill_and_accept):
            window.new_matrix_gate_action.trigger()
        self.assertTrue(window.gate_buttons["Rot"].isChecked())

        self.drop_gate("Rot", 0, 0)
        window.run_button.click()
        self.wait_for_editor()
        assert_allclose(window.session.result.amplitudes, [0.6, 0, 0.8, 0], atol=1e-12)

    def test_create_or_create_and_save(self):
        """Create adds an unsaved gate. Create and save… stays open after a cancel or failed write, then saves the gate with its base."""
        window = self.window
        self.create_gate(MatrixGateDialog, window.new_matrix_gate_action, "Rot")
        self.assertEqual(window.session.unsaved_gates, {"Rot"})
        self.assertEqual(list(self.data_directory.rglob("*.json")), [])

        saved = self.data_directory / "gates" / "CRot.json"

        def try_saving(dialog):
            dialog.base_choice.setCurrentText("Rot")
            # A cancelled file picker and a failed write both keep the dialog and its input.
            with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
                dialog.save_button.click()
            with (
                patch.object(QFileDialog, "getSaveFileName", return_value=(str(saved), "")),
                patch.object(Path, "replace", side_effect=OSError("disk full")),
                patch.object(QMessageBox, "warning"),
            ):
                dialog.save_button.click()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected.value)
            self.assertEqual(dialog.name_edit.text(), "CRot")

            with patch.object(QFileDialog, "getSaveFileName", return_value=(str(saved), "")):
                dialog.save_button.click()
            return dialog.result()

        with patch.object(ControlledGateDialog, "exec", try_saving):
            window.new_controlled_gate_action.trigger()
        self.assertEqual([definition.gate_id for definition in load_gates(saved)], ["Rot", "CRot"])
        self.assertEqual(window.session.unsaved_gates, set())

        # Opening the controlled gate's file elsewhere brings its base along. Neither can be edited.
        fresh = SimulatorWindow(self.data_directory / "other session")
        self.addCleanup(fresh.deleteLater)
        with (
            patch.object(QFileDialog, "getOpenFileName", return_value=(str(saved), "")),
            patch.object(QMessageBox, "information") as information,
        ):
            fresh.open_gate_action.trigger()
        information.assert_called_once()
        self.assertEqual([definition.gate_id for definition in fresh.session.library.user_definitions], ["Rot", "CRot"])
        self.assertEqual(fresh.circuit_title.text(), "Circuit: Untitled")


class TestGateFiles(WindowTestCase):
    """Open and save gate files through the File menu, resolve name clashes, and warn about unsaved gates."""

    def test_name_conflicts_and_bad_gate_files(self):
        """A clashing gate in an opened circuit is renamed or replaced by mine. A cancel or a bad gate file changes nothing."""
        window = self.window
        window._add_definition(MatrixGate("Rot", [[0.6, -0.8], [0.8, 0.6]]))
        broken = self.data_directory / "broken.json"
        broken.write_text(
            '{"kind": "gate_file", "version": 1, "definitions": '
            '[{"id": "CFoo", "kind": "controlled", "base": "Foo", "wire_count": 2}]}',
            encoding="utf-8",
        )
        with (
            patch.object(QFileDialog, "getOpenFileName", return_value=(str(broken), "")),
            patch.object(QMessageBox, "warning") as warning,
        ):
            window.open_gate_action.trigger()
        warning.assert_called_once()

        # This circuit's Rot is a different gate, so opening it asks what to do.
        self.drop_gate("H", 0, 0)
        other = self.data_directory / "other.json"
        other_rot = MatrixGate("Rot", [[0, 1], [1, 0]])
        save_circuit(other, Circuit(1, "0", (PlacedGate(0, "Rot", (0,)),), definitions=(other_rot,)))
        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(other), "")):
            with patch.object(SimulatorWindow, "_resolve_name_clash", return_value=None):
                window.open_action.trigger()
            self.assertEqual(window.session.gates, [PlacedGate(0, "H", (0,))])
            self.assertEqual([definition.gate_id for definition in window.session.library.user_definitions], ["Rot"])

            with patch.object(SimulatorWindow, "_resolve_name_clash", return_value="Flip"):
                window.open_action.trigger()
            self.assertEqual(window.session.gates, [PlacedGate(0, "Flip", (0,))])
            self.assertEqual(
                [definition.gate_id for definition in window.session.library.user_definitions], ["Rot", "Flip"]
            )
            self.assertIn("Flip", window.gate_buttons)

            # Flip came in from a circuit. Manage gates can save it on its own.
            flip_file = self.data_directory / "gates" / "Flip.json"

            def save_flip(dialog):
                dialog.select_gate("Flip")
                with patch.object(QFileDialog, "getSaveFileName", return_value=(str(flip_file), "")):
                    dialog.save_button.click()

            with patch.object(GateManagerDialog, "exec", save_flip):
                window.manage_gates_action.trigger()
            self.assertEqual([definition.gate_id for definition in load_gates(flip_file)], ["Flip"])
            self.assertNotIn("Flip", window.session.unsaved_gates)

            # Use mine: the circuit's Rot becomes the local one, so the circuit differs from its file.
            with patch.object(SimulatorWindow, "_resolve_name_clash", return_value=ClashChoice.USE_LOCAL):
                window.open_action.trigger()
        self.assertEqual(window.session.gates, [PlacedGate(0, "Rot", (0,))])
        self.assertEqual(window.session.library.matrix("Rot")[1, 0], 0.8)
        self.assertTrue(window.session.modified)

    def test_opening_a_gate_follows_the_gate_chosen(self):
        """Use mine with a local matrix gate keeps the open circuit and edits nothing. Cancel leaves the palette alone."""
        window = self.window
        window._add_definition(MatrixGate("Inner", [[0, 1], [1, 0]]))
        self.drop_gate("H", 0, 0)
        gate_file = self.data_directory / "Inner.json"
        save_gates(gate_file, [CircuitGate("Inner", 1, (GateOperation("H", (0,)),))])
        palette = list(window.gate_buttons)

        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(gate_file), "")):
            with patch.object(SimulatorWindow, "_resolve_name_clash", return_value=None):
                window.open_gate_action.trigger()
            self.assertEqual(list(window.gate_buttons), palette)

            with (
                patch.object(SimulatorWindow, "_resolve_name_clash", return_value=ClashChoice.USE_LOCAL),
                patch.object(QMessageBox, "information") as information,
                patch.object(QMessageBox, "question") as question,
            ):
                window.open_gate_action.trigger()
        information.assert_called_once()
        # Nothing replaces the circuit, so it is not even asked about.
        question.assert_not_called()
        self.assertEqual(window.circuit_title.text(), "Circuit: Untitled")
        self.assertEqual(window.session.gates, [PlacedGate(0, "H", (0,))])

    def test_saving_a_gate_keeps_the_other_gates_in_its_file(self):
        """Editing one of two independent gates in a file and saving it rewrites only that gate."""
        window = self.window
        first = CircuitGate("First", 1, (GateOperation("H", (0,)),))
        second = CircuitGate("Second", 1, (GateOperation("X", (0,)),))
        gate_file = self.data_directory / "pair.json"
        save_gates(gate_file, [first, second])

        with (
            patch.object(QFileDialog, "getOpenFileName", return_value=(str(gate_file), "")),
            patch.object(QInputDialog, "getItem", return_value=("First", True)),
        ):
            window.open_gate_action.trigger()
        self.assertEqual(window.circuit_title.text(), "Gate: First")
        window.session.delete_gate("Second")
        window._remove_gate_button("Second")
        self.drop_gate("Z", 1, 0)
        window.save_button.click()

        saved = {definition.gate_id: definition for definition in load_gates(gate_file)}
        self.assertEqual(saved["Second"], second)
        self.assertEqual(saved["First"].operations, (GateOperation("H", (0,)), GateOperation("Z", (0,))))

    def test_overwriting_last_saved_copy_restores_close_warning(self):
        """A gate survives overwriting one copy, but losing its last file triggers the close warning."""
        window = self.window
        window._add_definition(MatrixGate("Flip", [[0, 1], [1, 0]]))
        window._add_definition(MatrixGate("Phase", [[1, 0], [0, -1]]))
        self.drop_gate("Flip", 0, 0)
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(window.saved_circuits / "demo.json"), "")):
            window.save_button.click()
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(self.data_directory / "gate.json"), "")):
            window._save_gate_as("Flip")
            window._save_gate_as("Phase")
        self.assertFalse(window.session.unsaved_gates)
        self.right_click_cell(0, 0)
        with (
            patch.object(QInputDialog, "getText", return_value=("demo", True)),
            patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes),
        ):
            window.save_button.click()
        self.assertEqual(window.session.unsaved_gates, {"Flip"})
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel) as question:
            window.close()
        question.assert_called_once()
        self.assertTrue(window.isVisible())

    def test_closing_asks_about_gates_saved_nowhere(self):
        """Closing asks before losing a custom gate that no saved file holds. Saving a circuit that uses it settles it."""
        window = self.window
        window._add_definition(MatrixGate("Rot", [[0.6, -0.8], [0.8, 0.6]]))
        window._add_definition(MatrixGate("Flip", [[0, 1], [1, 0]]))
        self.drop_gate("Rot", 0, 0)
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(window.saved_circuits / "demo.json"), "")):
            window.save_action.trigger()
        self.assertEqual(window.session.unsaved_gates, {"Flip"})

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel) as question:
            window.close()
        question.assert_called_once()
        self.assertTrue(window.isVisible())

        self.drop_gate("Flip", 1, 0)
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(window.saved_circuits / "with flip.json"), "")):
            window.save_as_action.trigger()
        with patch.object(QMessageBox, "question") as question:
            window.close()
        question.assert_not_called()
        self.assertFalse(window.isVisible())


class TestUnsavedChanges(WindowTestCase):
    """Ask before unsaved edits or placed gates are lost."""

    def test_prompt_before_replacing_unsaved_changes(self):
        """Opening, starting a new circuit or closing asks first. Cancel keeps the circuit, and Don't save goes ahead."""
        window = self.window
        self.drop_gate("H", 0, 0)
        cancel = QMessageBox.StandardButton.Cancel
        with patch.object(QMessageBox, "question", return_value=cancel) as question:
            window.examples_menu.actions()[0].trigger()
            window.new_circuit_action.trigger()
            window.close()
        self.assertEqual(question.call_count, 3)
        self.assertEqual(window.session.gates, [PlacedGate(0, "H", (0,))])
        self.assertTrue(window.isVisible())

        # The test setup answers Don't save, so the example replaces the circuit.
        window.examples_menu.actions()[0].trigger()
        self.assertEqual([gate.name for gate in window.session.gates], ["H", "CNOT"])
        self.assertFalse(window.session.modified)

    def test_lowering_qubits_asks_before_removing_gates(self):
        """Lowering the qubit count asks before removing gates. Cancel keeps them, and OK removes them."""
        window = self.window
        window.qubit_count.setValue(3)
        self.drop_gate("H", 0, 0)
        self.drop_gate("X", 0, 2)

        cancel = QMessageBox.StandardButton.Cancel
        with patch.object(QMessageBox, "question", return_value=cancel) as question:
            window.qubit_count.setValue(2)
        question.assert_called_once()
        self.assertEqual(window.qubit_count.value(), 3)
        self.assertEqual(len(window.session.gates), 2)

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Ok):
            window.qubit_count.setValue(2)
        self.assertEqual(window.session.gates, [PlacedGate(0, "H", (0,))])


class TestGateManager(WindowTestCase):
    """Inspect gates and delete custom ones through Gates → Manage gates."""

    def test_custom_gate_can_be_deleted_only_after_removing_it(self):
        """A placed custom gate shows its matrix but cannot be deleted until it is removed from the circuit."""
        window = self.window
        window._add_definition(MatrixGate("Rot", [[0.6, -0.8], [0.8, 0.6]]))
        self.drop_gate("Rot", 0, 0)

        def check_blocked(dialog):
            dialog.select_gate("Rot")
            self.assertEqual(dialog.matrix.item(1, 0).text(), "0.8")
            self.assertFalse(dialog.delete_button.isEnabled())
            self.assertIn("Remove Rot from the circuit", dialog.delete_reason.text())

        def delete(dialog):
            dialog.select_gate("Rot")
            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                dialog.delete_button.click()

        # Replacing exec with a plain function makes it receive the real dialog the window opens.
        with patch.object(GateManagerDialog, "exec", check_blocked):
            window.manage_gates_action.trigger()
        self.right_click_cell(0, 0)
        with patch.object(GateManagerDialog, "exec", delete):
            window.manage_gates_action.trigger()
        self.assertNotIn("Rot", window.gate_buttons)
        self.assertNotIn("Rot", window.session.library)

    def test_large_gate_shows_a_note_instead_of_its_matrix(self):
        """A six-wire gate shows a note instead of building its 64×64 matrix table."""
        session = self.window.session
        session.library.add(
            MatrixGate("U3", np.eye(8)),
            ControlledGate("C4", "U3", 4),
            ControlledGate("C5", "C4", 5),
            ControlledGate("C6", "C5", 6),
        )
        dialog = GateManagerDialog(session, self.window)
        self.addCleanup(dialog.deleteLater)

        dialog.select_gate("C6")
        self.assertTrue(dialog.matrix.isHidden())
        self.assertEqual(dialog.matrix.rowCount(), 0)
        self.assertIn("64×64", dialog.matrix_note.text())


class TechnicalTests(WindowTestCase):
    """Check Run, Measure, error recovery, the qubit limit, and closing a busy window."""

    def test_typed_count_above_twenty_qubits_is_refused(self):
        """Typing 25 qubits shows a warning and keeps 2 qubits, so no oversized state is built."""
        window = self.window
        window.qubit_count.lineEdit().selectAll()
        with patch.object(QMessageBox, "warning") as warning:
            QTest.keyClicks(window.qubit_count, "25")
            QTest.keyClick(window.qubit_count, Qt.Key.Key_Return)

        warning.assert_called_once()
        self.assertEqual(window.qubit_count.value(), 2)
        self.assertEqual(window.session.qubits, 2)

    def test_run_then_measure(self):
        """Run shows loading, then the Bell pair can be measured."""
        window = self.window
        window.circuit_view.gate_dropped.emit("H", 0, 0)
        window.circuit_view.gate_dropped.emit("CNOT", 1, 0)
        window.circuit_view.gate_dropped.emit("CNOT", 1, 1)
        window.run_button.click()
        self.assertTrue(window.loading_screen.isVisible())
        self.assertFalse(window.measure_button.isEnabled())
        self.wait_for_editor()

        table = window.results_table
        self.assertEqual(table.rowCount(), 2)
        for row, basis in enumerate(("00", "11")):
            self.assertEqual(table.item(row, 0).text(), basis)
            self.assertEqual(table.item(row, 1).text(), "0.7071")
            self.assertEqual(table.item(row, 2).text(), "50.00%")
        window.measure_button.click()
        self.assertEqual(table.rowCount(), 1)
        self.assertIn(table.item(0, 0).text(), ("00", "11"))
        self.assertEqual(table.item(0, 2).text(), "100.00%")

    def test_retry_after_error(self):
        """A failed run returns to the editor and can be retried."""
        window = self.window
        window.circuit_view.gate_dropped.emit("X", 0, 0)
        with patch.object(QuantumState, "apply_gate", side_effect=ValueError("invalid gate")):
            window.run_button.click()
            self.wait_for_editor()
        self.assertIn("invalid gate", window.result_summary.text())
        self.assertFalse(window.measure_button.isEnabled())
        window.run_button.click()
        self.wait_for_editor()
        self.assertEqual(window.results_table.item(0, 0).text(), "10")

    def test_close_during_run(self):
        """Closing during a run discards unfinished results."""
        window = self.window
        window.run_button.click()
        window.close()
        window.show()
        self.assertFalse(window.loading_screen.isVisible())
        self.assertFalse(window._run_timer.isActive())
        self.assertFalse(window.measure_button.isEnabled())
        self.assertEqual(window.results_table.rowCount(), 0)


class TestWindowLayout(WindowTestCase):
    """Check the fixed parts of the editor layout."""

    def test_logo_below_results(self):
        """The course logo loads at its fixed height below the results."""
        window = self.window
        logo = window.logo.icon().pixmap(window.logo.iconSize(), window.logo.devicePixelRatioF())
        self.assertFalse(logo.isNull())
        self.assertEqual(round(logo.deviceIndependentSize().height()), 44)

        table = window.results_table
        table_bottom = table.mapTo(window, table.rect().bottomLeft()).y()
        self.assertGreater(window.logo.mapTo(window, window.logo.rect().topLeft()).y(), table_bottom)


class TestMemoryLifetime(WindowTestCase):
    """Check that discarded simulation states and native Qt timers are released."""

    def test_replacing_and_clearing_results(self):
        """Rerunning and clearing release previous states."""
        window = self.window
        window.circuit_view.gate_dropped.emit("H", 0, 0)
        results = []
        for _ in range(3):
            window.run_button.click()
            self.wait_for_editor()
            # A weak reference lets the test observe a state without keeping it alive.
            results.append(weakref.ref(window.session.result))

        gc.collect()
        for previous in results[:-1]:
            self.assertIsNone(previous())
        current = results[-1]
        self.assertIsNotNone(current())
        self.assertTrue(window.measure_button.isEnabled())

        window.clear_button.click()
        gc.collect()
        self.assertIsNone(current())

    def test_disposing_window_destroys_run_timer(self):
        """Disposing of a busy window destroys its timer."""
        window = self.window
        window_destroyed = QSignalSpy(window.destroyed)
        timer_destroyed = QSignalSpy(window._run_timer.destroyed)
        window.run_button.click()
        self.assertTrue(window._run_timer.isActive())

        self.dispose_window()

        self.assertEqual(window_destroyed.count(), 1)
        self.assertEqual(timer_destroyed.count(), 1)

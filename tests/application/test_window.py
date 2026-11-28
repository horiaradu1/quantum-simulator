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
from quantum_simulator.gui.gate_button import GATE_MIME_TYPE
from quantum_simulator.gui.gate_dialogs import MatrixGateDialog
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

        self.window = SimulatorWindow()
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

    def test_save_clear_open_and_run(self):
        """A saved circuit reopens after Clear and runs the same. An invalid file leaves it open."""
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
        with patch.object(QInputDialog, "getText", return_value=("demo", True)):
            window.save_action.trigger()

        window.clear_button.click()
        window.qubit_count.setValue(2)
        saved_file = str(window.saved_circuits / "demo.json")
        with patch.object(QFileDialog, "getOpenFileName", return_value=(saved_file, "")):
            window.open_action.trigger()
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


class TestUnsavedChanges(WindowTestCase):
    """Ask before unsaved edits or placed gates are lost."""

    def test_prompt_before_replacing_unsaved_changes(self):
        """Opening, clearing or closing asks first. Cancel keeps the circuit, and Don't save goes ahead."""
        window = self.window
        self.drop_gate("H", 0, 0)
        cancel = QMessageBox.StandardButton.Cancel
        with patch.object(QMessageBox, "question", return_value=cancel) as question:
            window.examples_menu.actions()[0].trigger()
            window.clear_button.click()
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

    def test_symbol_preview_never_outlines_a_cell(self):
        """With the pointer resting on the symbol preview, choosing another gate by keyboard outlines no cell."""
        dialog = GateManagerDialog(self.window.session, self.window)
        self.addCleanup(dialog.close)
        dialog.show()
        QTest.qWaitForWindowExposed(dialog)
        preview = dialog.preview
        QTest.mouseMove(preview.viewport(), preview.mapFromScene(preview.cell_center(0, 0)))

        QTest.keyClick(dialog.gate_list, Qt.Key.Key_Down)
        self.assertEqual(dialog.gate_list.currentItem().text(), "X")
        self.assertIsNone(preview.highlighted_cell)

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

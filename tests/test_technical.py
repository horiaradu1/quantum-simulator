"""Exercise gate placement, the desktop Run workflow, and cleanup after simulation."""

import gc
import os
import unittest
import weakref
from unittest.mock import patch

from PySide6.QtCore import QEvent
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from quantum_simulator.backend import QuantumState
from quantum_simulator.gui.window import SimulatorWindow


class WindowTestCase(unittest.TestCase):
    """Open an offscreen simulator window for each test."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
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


class TestGatePlacement(WindowTestCase):
    """Check how wire selections become complete gates in the editor."""

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
        self.assertIn("target in step 1", window.circuit_hint.text())

        grid.cell_clicked.emit(1, 1)
        self.assertIn("second control in step 2", window.circuit_hint.text())
        grid.cell_clicked.emit(1, 2)
        grid.cell_clicked.emit(1, 0)

        window.run_button.click()
        self.wait_for_editor()
        self.assertEqual(window.results_table.item(0, 0).text(), "111")


class TechnicalTests(WindowTestCase):
    """Check Run, Measure, error recovery, and closing a busy window."""

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
            results.append(weakref.ref(window._result_state))

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

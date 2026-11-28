"""Check how the circuit canvas draws gate symbols on their wires."""

import os
import unittest

import numpy as np
from PySide6.QtCore import QMimeData, QPointF, Qt
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
)

from quantum_simulator.backend.circuit import PlacedGate
from quantum_simulator.backend.gate_library import ControlledGate, GateLibrary, MatrixGate
from quantum_simulator.gui.circuit_view import CircuitView
from quantum_simulator.gui.gate_button import GATE_MIME_TYPE

_WIRES = 4


class TestGateSymbols(unittest.TestCase):
    """Draw one gate on a four-wire canvas and inspect the items on each wire."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def draw_gate(self, gate, library=None):
        view = CircuitView(library=library)
        self.addCleanup(view.deleteLater)
        view.render_circuit(n_qubits=_WIRES, gates=[gate])
        return view

    @staticmethod
    def items_at_cell(view, step, wire, item_type):
        items = view.scene().items(view.cell_center(step, wire))
        return [item for item in items if isinstance(item, item_type)]

    @staticmethod
    def wire_at(view, y):
        for wire in range(_WIRES):
            if abs(view.cell_center(0, wire).y() - y) < 1:
                return wire
        return None

    def box_texts(self, view):
        """Return the only box's name and the text it shows on each wire."""
        boxes = [item for item in view.scene().items() if isinstance(item, QGraphicsRectItem)]
        self.assertEqual(len(boxes), 1)
        box = boxes[0].sceneBoundingRect()

        labels = []
        wire_marks = {}
        for item in view.scene().items():
            if not isinstance(item, QGraphicsSimpleTextItem):
                continue
            center = item.sceneBoundingRect().center()
            if not box.contains(center):
                continue
            wire = self.wire_at(view, center.y())
            if wire is None:
                labels.append(item.text())
            else:
                wire_marks[wire] = item.text()
        return labels, wire_marks

    def test_cy_draws_control_dot_and_y_box(self):
        """CY from q3 to q0 draws a control dot on q3, a Y box on q0, and no symbol on q1 or q2."""
        view = self.draw_gate(PlacedGate(0, "CY", (3, 0)))

        self.assertEqual(len(self.items_at_cell(view, 0, 3, QGraphicsEllipseItem)), 1)
        self.assertEqual(self.items_at_cell(view, 0, 3, QGraphicsRectItem), [])

        target_labels = [item.text() for item in self.items_at_cell(view, 0, 0, QGraphicsSimpleTextItem)]
        self.assertEqual(target_labels, ["Y"])
        self.assertEqual(len(self.items_at_cell(view, 0, 0, QGraphicsRectItem)), 1)
        self.assertEqual(self.items_at_cell(view, 0, 0, QGraphicsEllipseItem), [])

        for wire in (1, 2):
            for item_type in (QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsSimpleTextItem):
                with self.subTest(wire=wire, item=item_type.__name__):
                    self.assertEqual(self.items_at_cell(view, 0, wire, item_type), [])

    def test_gate_without_symbol_marks_only_its_wires(self):
        """A two-wire matrix gate on q3 and q0 numbers those wires in gate order and leaves q1 and q2 unmarked."""
        library = GateLibrary([MatrixGate("U2", np.eye(4))])
        view = self.draw_gate(PlacedGate(0, "U2", (3, 0)), library)

        labels, wire_marks = self.box_texts(view)
        self.assertEqual(labels, ["U2"])
        self.assertEqual(wire_marks, {3: "0", 0: "1"})

    def test_controlled_matrix_gate_draws_control_dot_and_base_box(self):
        """CU2 with its control on q3 draws a dot there and a U2 box on q0 and q1, numbered 1 and 2."""
        library = GateLibrary([MatrixGate("U2", np.eye(4)), ControlledGate("CU2", "U2", 3)])
        view = self.draw_gate(PlacedGate(0, "CU2", (3, 0, 1)), library)

        self.assertEqual(len(self.items_at_cell(view, 0, 3, QGraphicsEllipseItem)), 1)
        self.assertEqual(self.items_at_cell(view, 0, 3, QGraphicsRectItem), [])
        labels, wire_marks = self.box_texts(view)
        self.assertEqual(labels, ["U2"])
        self.assertEqual(wire_marks, {0: "1", 1: "2"})


class TestCellHighlight(unittest.TestCase):
    """Check which cell the canvas outlines when it redraws under a still pointer."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def test_redraw_keeps_hover_and_drag_rules(self):
        """Hover outlines an occupied cell, but a gate dragged onto it outlines nothing, even after a redraw."""
        view = CircuitView()
        self.addCleanup(view.deleteLater)
        view.show()
        QTest.qWaitForWindowExposed(view)
        gates = [PlacedGate(0, "X", (0,))]
        view.render_circuit(n_qubits=2, gates=gates)
        pointer = view.mapFromScene(view.cell_center(0, 0))
        QTest.mouseMove(view.viewport(), pointer)
        self.assertEqual(view.highlighted_cell, (0, 0))

        mime = QMimeData()
        mime.setData(GATE_MIME_TYPE, b"H")
        drag = (Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(view.viewport(), QDragEnterEvent(QPointF(pointer), *drag))
        view.render_circuit(n_qubits=2, gates=gates)
        self.assertIsNone(view.highlighted_cell)

        QApplication.sendEvent(view.viewport(), QDragLeaveEvent())
        view.render_circuit(n_qubits=2, gates=gates)
        self.assertEqual(view.highlighted_cell, (0, 0))

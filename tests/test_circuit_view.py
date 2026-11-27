"""Check how the circuit canvas draws gate symbols on their wires."""

import os
import unittest

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
)

from quantum_simulator.backend.gate_catalog import GATE_CATALOG, GateSpec
from quantum_simulator.gui.circuit_view import CircuitView, PlacedGate

_WIRES = 4


class TestGateSymbols(unittest.TestCase):
    """Draw one gate on a four-wire canvas and inspect the items on each wire."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def draw_gate(self, gate, catalog=GATE_CATALOG):
        view = CircuitView(catalog=catalog)
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
        """A named box on q3 and q0 numbers those wires in gate order and leaves q1 and q2 unmarked."""
        catalog = {"PAIR": GateSpec("PAIR", ("first wire", "second wire"))}
        view = self.draw_gate(PlacedGate(0, "PAIR", (3, 0)), catalog)

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

        self.assertEqual(labels, ["PAIR"])
        self.assertEqual(wire_marks, {3: "0", 0: "1"})

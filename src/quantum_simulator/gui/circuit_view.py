"""Draw the circuit grid and translate clicks and gate drops into wire and step positions."""

from collections.abc import Mapping, Sequence
from math import floor

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView, QWidget

from ..backend.circuit import PlacedGate
from ..backend.gate_catalog import GATE_CATALOG, GateSpec, WireMark
from .gate_button import GATE_MIME_TYPE
from .styles import ACCENT, BORDER, INK, LAVENDER, SURFACE

_MIN_STEPS = 8
_GRID_LEFT = 64
_GRID_TOP = 32
_GRID_PADDING = 16
_STEP_WIDTH = 86
_WIRE_HEIGHT = 64
_BOX_SIZE = 34
_NAMED_BOX_WIDTH = 62

_CANVAS = QColor("#fcfbff")
_GRID = QColor(BORDER)
_WIRE = QColor("#6d647d")
_INK = QColor(INK)
_ACCENT = QColor(ACCENT)
_GATE_FILL = QColor(SURFACE)
_PENDING_WIRE = QColor(LAVENDER)


class CircuitView(QGraphicsView):
    """Display a scrollable circuit and signal edits to the main window."""

    cell_clicked = Signal(int, int)
    cell_removed = Signal(int, int)
    gate_dropped = Signal(str, int, int)

    def __init__(
        self, parent: QWidget | None = None, *, catalog: Mapping[str, GateSpec] = GATE_CATALOG
    ):
        super().__init__(parent)
        self._catalog = catalog
        self._n_qubits = 0
        self._steps = _MIN_STEPS
        self._gates: tuple[PlacedGate, ...] = ()
        self._pending_step: int | None = None
        self._pending_wires: tuple[int, ...] = ()
        self._drop_cell: tuple[int, int] | None = None

        self.setScene(QGraphicsScene(self))
        self.setObjectName("circuitGrid")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setBackgroundBrush(QBrush(_CANVAS))
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAccessibleName("Circuit grid")
        self.viewport().setAcceptDrops(True)

    def cell_center(self, step: int, wire: int) -> QPointF:
        """Convert a step and wire into a point in the scrollable scene."""
        return QPointF(
            _GRID_LEFT + (step + 0.5) * _STEP_WIDTH,
            _GRID_TOP + (wire + 0.5) * _WIRE_HEIGHT,
        )

    def render_circuit(
        self,
        *,
        n_qubits: int,
        gates: Sequence[PlacedGate],
        pending_step: int | None = None,
        pending_wires: tuple[int, ...] = (),
    ) -> None:
        self._preview_drop(None)
        self._n_qubits = n_qubits
        self._gates = tuple(gates)
        self._pending_step = pending_step
        self._pending_wires = pending_wires
        self._draw_circuit(self._step_count())

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._preview_drop(None)
        steps = self._step_count()
        if self._n_qubits and steps != self._steps:
            self._draw_circuit(steps)

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self._preview_drop(None)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            super().wheelEvent(event)
            return

        pixels = event.pixelDelta()
        distance = pixels.x() or pixels.y()
        if not distance:
            angle = event.angleDelta()
            # A standard wheel notch is 120 angle units. Move one column per notch.
            distance = round((angle.x() or angle.y()) * _STEP_WIDTH / 120)

        scrollbar = self.horizontalScrollBar()
        scrollbar.setValue(scrollbar.value() - distance)
        event.accept()

    def _step_count(self) -> int:
        available_width = self.viewport().width() - _GRID_LEFT - _GRID_PADDING
        visible_steps = available_width // _STEP_WIDTH
        last_step = max((gate.step for gate in self._gates), default=-1)
        # Keep one empty column after the last gate so the circuit can keep growing.
        steps_after_edit = last_step + 2
        pending_steps = 0 if self._pending_step is None else self._pending_step + 1
        return max(_MIN_STEPS, visible_steps, steps_after_edit, pending_steps)

    def _draw_circuit(self, steps: int) -> None:
        self._steps = steps
        right = _GRID_LEFT + self._steps * _STEP_WIDTH
        bottom = _GRID_TOP + self._n_qubits * _WIRE_HEIGHT

        scene = self.scene()
        scene.clear()
        if self._pending_step is not None:
            x = _GRID_LEFT + self._pending_step * _STEP_WIDTH
            scene.addRect(
                x, _GRID_TOP, _STEP_WIDTH, bottom - _GRID_TOP,
                QPen(Qt.PenStyle.NoPen), QBrush(QColor("#f4f0ff")),
            )

        self._draw_grid(right, bottom)

        if self._pending_step is not None:
            for wire in self._pending_wires:
                x, y = self.cell_center(self._pending_step, wire).toTuple()
                scene.addEllipse(
                    x - 12, y - 12, 24, 24, QPen(_ACCENT, 1.5), QBrush(_PENDING_WIRE),
                )

        for gate in self._gates:
            self._draw_gate(gate)
        scene.setSceneRect(0, 0, right + _GRID_PADDING, bottom + _GRID_PADDING)

    def _draw_grid(self, right: int, bottom: int) -> None:
        scene = self.scene()
        grid_pen = QPen(_GRID, 1, Qt.PenStyle.DashLine)
        for step in range(self._steps + 1):
            x = _GRID_LEFT + step * _STEP_WIDTH
            scene.addLine(x, _GRID_TOP, x, bottom, grid_pen)

        for step in range(self._steps):
            x = self.cell_center(step, 0).x()
            self._add_label(str(step + 1), QPointF(x, _GRID_TOP / 2), 9, _WIRE)

        wire_pen = QPen(_WIRE, 1.25)
        for wire in range(self._n_qubits):
            y = self.cell_center(0, wire).y()
            scene.addLine(_GRID_LEFT, y, right, y, wire_pen)
            self._add_label(f"q{wire}", QPointF(_GRID_LEFT / 2, y), 11, _WIRE)

    def _cell_at(self, position: QPoint) -> tuple[int, int] | None:
        # Scene coordinates account for the current scroll position.
        point = self.mapToScene(position)
        step = floor((point.x() - _GRID_LEFT) / _STEP_WIDTH)
        wire = floor((point.y() - _GRID_TOP) / _WIRE_HEIGHT)
        if 0 <= step < self._steps and 0 <= wire < self._n_qubits:
            return step, wire
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        cell = self._cell_at(event.position().toPoint())
        if cell is not None:
            if event.button() == Qt.MouseButton.LeftButton:
                self.cell_clicked.emit(*cell)
                event.accept()
                return
            if event.button() == Qt.MouseButton.RightButton:
                self.cell_removed.emit(*cell)
                event.accept()
                return
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._gate_name(event) is None:
            self._preview_drop(None)
            event.ignore()
            return

        # Accept entry over the viewport margin so a drag can move onto the grid.
        self._preview_drop(self._available_cell_at(event.position().toPoint()))
        self._accept_copy(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        cell = None
        if self._gate_name(event) is not None:
            cell = self._available_cell_at(event.position().toPoint())
        self._preview_drop(cell)
        if cell is None:
            event.ignore()
        else:
            self._accept_copy(event)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._preview_drop(None)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self._preview_drop(None)
        name = self._gate_name(event)
        cell = self._available_cell_at(event.position().toPoint())
        if name is None or cell is None:
            event.ignore()
            return
        self.gate_dropped.emit(name, *cell)
        self._accept_copy(event)

    @staticmethod
    def _gate_name(event: QDropEvent) -> str | None:
        mime = event.mimeData()
        if not mime.hasFormat(GATE_MIME_TYPE) or not event.possibleActions() & Qt.DropAction.CopyAction:
            return None
        try:
            return bytes(mime.data(GATE_MIME_TYPE)).decode("utf-8") or None
        except UnicodeDecodeError:
            return None

    @staticmethod
    def _accept_copy(event: QDropEvent) -> None:
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def _available_cell_at(self, position: QPoint) -> tuple[int, int] | None:
        cell = self._cell_at(position)
        if cell is None:
            return None
        step, wire = cell
        if any(gate.step == step and wire in gate.wire_span for gate in self._gates):
            return None
        return cell

    def _preview_drop(self, cell: tuple[int, int] | None) -> None:
        if self._drop_cell != cell:
            self._drop_cell = cell
            self.viewport().update()

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawForeground(painter, rect)
        if self._drop_cell is None:
            return
        center = self.cell_center(*self._drop_cell)
        width, height = _STEP_WIDTH - 10, _WIRE_HEIGHT - 10
        outline = QRectF(center.x() - width / 2, center.y() - height / 2, width, height)
        painter.save()
        fill = QColor(_ACCENT)
        fill.setAlpha(24)
        painter.setPen(QPen(_ACCENT, 2))
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(outline, 6, 6)
        painter.restore()

    def _draw_gate(self, gate: PlacedGate) -> None:
        spec = self._catalog[gate.name]
        if spec.symbols is not None:
            self._draw_symbols(gate, spec.symbols)
        elif len(gate.wires) == 1:
            self._add_box(spec.label, self.cell_center(gate.step, gate.wires[0]))
        else:
            self._draw_named_box(gate, spec.label)

    def _draw_symbols(self, gate: PlacedGate, symbols: Sequence[WireMark | str]) -> None:
        points = [self.cell_center(gate.step, wire) for wire in gate.wires]
        pen = QPen(_ACCENT, 1.75)
        if len(points) > 1:
            rows = [point.y() for point in points]
            x = points[0].x()
            self.scene().addLine(x, min(rows), x, max(rows), pen)

        for point, symbol in zip(points, symbols, strict=True):
            match symbol:
                case WireMark.CONTROL:
                    self._add_control(point, pen)
                case WireMark.NOT:
                    self._add_not(point, pen)
                case WireMark.SWAP:
                    self._add_swap(point, pen)
                case str(text):
                    self._add_box(text, point)

    def _draw_named_box(self, gate: PlacedGate, label: str) -> None:
        rows = [self.cell_center(gate.step, wire).y() for wire in gate.wires]
        x = self.cell_center(gate.step, 0).x()
        left = x - _NAMED_BOX_WIDTH / 2
        top = min(rows) - _BOX_SIZE / 2
        bottom = max(rows) + _BOX_SIZE / 2
        self.scene().addRect(
            left, top, _NAMED_BOX_WIDTH, bottom - top, QPen(_ACCENT, 1.5), QBrush(_GATE_FILL),
        )
        self._add_label(label, QPointF(x, (top + bottom) / 2), 12, _INK)

        # Number the participating wires in gate order. Other wires inside the box stay unmarked.
        for position, y in enumerate(rows):
            self._add_label(str(position), QPointF(left + 8, y), 8, _ACCENT)

    def _add_control(self, center: QPointF, pen: QPen) -> None:
        self.scene().addEllipse(center.x() - 4, center.y() - 4, 8, 8, pen, QBrush(_ACCENT))

    def _add_not(self, center: QPointF, pen: QPen) -> None:
        x, y = center.toTuple()
        scene = self.scene()
        scene.addEllipse(x - 11, y - 11, 22, 22, pen, QBrush(_GATE_FILL))
        scene.addLine(x - 7, y, x + 7, y, pen)
        scene.addLine(x, y - 7, x, y + 7, pen)

    def _add_swap(self, center: QPointF, pen: QPen) -> None:
        x, y = center.toTuple()
        scene = self.scene()
        scene.addLine(x - 8, y - 8, x + 8, y + 8, pen)
        scene.addLine(x - 8, y + 8, x + 8, y - 8, pen)

    def _add_box(self, label: str, center: QPointF) -> None:
        half = _BOX_SIZE / 2
        self.scene().addRect(
            center.x() - half, center.y() - half, _BOX_SIZE, _BOX_SIZE,
            QPen(_ACCENT, 1.5), QBrush(_GATE_FILL),
        )
        self._add_label(label, center, 12, _INK)

    def _add_label(self, label: str, center: QPointF, size: int, color: QColor) -> None:
        font = self.font()
        font.setPointSize(size)
        font.setWeight(QFont.Weight.DemiBold)
        text = self.scene().addSimpleText(label, font)
        text.setBrush(QBrush(color))
        bounds = text.boundingRect()
        text.setPos(center.x() - bounds.width() / 2, center.y() - bounds.height() / 2)

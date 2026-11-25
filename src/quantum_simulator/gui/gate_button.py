"""Provide the draggable gate buttons in the circuit editor's palette."""

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import QApplication, QPushButton


GATE_MIME_TYPE = "application/x-quantum-simulator-gate"


class GateButton(QPushButton):
    """Carry the gate name from the palette to a drop target on the circuit."""

    def __init__(self, gate_name: str):
        super().__init__("Toffoli" if gate_name == "TOFFOLI" else gate_name)
        self.gate_name = gate_name
        self._press_position: QPoint | None = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip(f"Drag {self.text()} onto a circuit wire")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        press_position = self._press_position
        if press_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            distance = (event.position().toPoint() - press_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self._press_position = None
                self.setDown(False)
                self._start_drag(press_position)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = None
        super().mouseReleaseEvent(event)

    def _start_drag(self, press_position: QPoint) -> None:
        mime_data = QMimeData()
        mime_data.setData(GATE_MIME_TYPE, self.gate_name.encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(press_position)
        drag.exec(Qt.DropAction.CopyAction)

"""Provide the arrow buttons shared by the qubit count and binary state inputs."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QProxyStyle, QSpinBox, QStyle

from .styles import ACCENT


class _SpinArrowStyle(QProxyStyle):
    """Draw the up and down triangles using the simulator's accent color."""

    def drawPrimitive(self, element, option, painter, widget=None):
        up = QStyle.PrimitiveElement.PE_IndicatorSpinUp
        down = QStyle.PrimitiveElement.PE_IndicatorSpinDown
        if element not in (up, down):
            super().drawPrimitive(element, option, painter, widget)
            return

        center = QRectF(option.rect).center()
        direction = -1 if element == up else 1
        arrow = QPolygonF([
            center + QPointF(-4.5, -direction * 2.5),
            center + QPointF(4.5, -direction * 2.5),
            center + QPointF(0, direction * 2.5),
        ])
        color = QColor(ACCENT)
        if not option.state & QStyle.StateFlag.State_Enabled:
            color.setAlpha(120)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(arrow)
        painter.restore()


class ArrowSpinBox(QSpinBox):
    """A spin box with arrows drawn at a consistent size."""

    def __init__(self):
        super().__init__()
        style = _SpinArrowStyle("Fusion")
        style.setParent(self)
        self.setStyle(style)

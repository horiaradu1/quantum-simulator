"""Show every gate, what it does and how it is drawn. Save any custom gate, and delete those that nothing uses."""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..backend.circuit import PlacedGate
from ..backend.editor import EditorSession
from ..backend.expressions import format_complex
from .circuit_view import CircuitView

_GATE_ID_ROLE = Qt.ItemDataRole.UserRole
_LIST_WIDTH = 170
_NOTE_COLOR = "#60576f"
_PREVIEW_MARGIN = 8
_MAX_SHOWN_MATRIX_WIRES = 5


def _numbered_wires(wire_roles: tuple[str, ...]) -> str:
    """Number each wire with its role, such as 0 – control, 1 – target."""
    # The number already gives the order, so "second control" is shown as "control".
    kinds = [role.split()[-1] for role in wire_roles]
    return ", ".join(f"{position} – {kind}" for position, kind in enumerate(kinds))


def _heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-weight: 600;")
    return label


class GateManagerDialog(QDialog):
    """List every gate with its description, symbol and matrix, and delete unused custom gates."""

    gate_deleted = Signal(str)

    def __init__(
        self, session: EditorSession, parent: QWidget | None = None,
        save_gate: Callable[[str], object] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Manage gates")
        self.setMinimumSize(860, 600)
        self._session = session

        self.gate_list = QListWidget()
        self.gate_list.setFixedWidth(_LIST_WIDTH)
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 17px; font-weight: 700; color: #382967;")
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.wires = QLabel()

        # The real circuit canvas draws the symbol, so the preview matches the circuit.
        self.preview = CircuitView(library=session.library, editable=False)
        self.preview.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.matrix = QTableWidget()
        self.matrix.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.matrix.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.matrix_note = QLabel()
        self.matrix_note.setStyleSheet(f"color: {_NOTE_COLOR};")

        self.usage = QLabel()
        self.delete_button = QPushButton("Delete gate")
        self.delete_button.clicked.connect(self._delete_selected)
        self.save_button = QPushButton("Save gate as…")
        self.save_button.setVisible(save_gate is not None)
        if save_gate is not None:
            self.save_button.clicked.connect(lambda: save_gate(self._selected_gate()))
        self.delete_reason = QLabel()
        self.delete_reason.setStyleSheet(f"color: {_NOTE_COLOR};")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        details = QVBoxLayout()
        details.addWidget(self.title)
        details.addWidget(self.description)
        details.addWidget(self.wires)
        details.addSpacing(6)

        symbol = QVBoxLayout()
        symbol.addWidget(_heading("Symbol"))
        symbol.addWidget(self.preview)
        symbol.addStretch()
        matrix = QVBoxLayout()
        matrix.addWidget(_heading("Matrix: columns are input states, rows are output states"))
        matrix.addWidget(self.matrix_note)
        matrix.addWidget(self.matrix, 1)
        matrix.addStretch()
        pictures = QHBoxLayout()
        pictures.addLayout(symbol)
        pictures.addSpacing(12)
        pictures.addLayout(matrix, 1)
        details.addLayout(pictures, 1)

        details.addWidget(self.usage)
        delete_row = QHBoxLayout()
        delete_row.addWidget(self.save_button)
        delete_row.addWidget(self.delete_button)
        delete_row.addWidget(self.delete_reason, 1)
        details.addLayout(delete_row)

        content = QHBoxLayout()
        content.addWidget(self.gate_list)
        content.addLayout(details, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(content, 1)
        layout.addWidget(buttons)

        self.gate_list.currentItemChanged.connect(self._show_selected)
        self._fill_list()

    def select_gate(self, gate_id: str) -> None:
        for row in range(self.gate_list.count()):
            item = self.gate_list.item(row)
            if item.data(_GATE_ID_ROLE) == gate_id:
                self.gate_list.setCurrentItem(item)
                return

    def _fill_list(self) -> None:
        library = self._session.library
        builtin_ids = [gate_id for gate_id in library.gate_ids() if library.is_builtin(gate_id)]
        custom_ids = [definition.gate_id for definition in library.user_definitions]

        self.gate_list.clear()
        for heading, gate_ids in (("Built-in gates", builtin_ids), ("Custom gates", custom_ids)):
            self._add_heading(heading)
            if not gate_ids:
                self._add_heading("None yet", bold=False)
            for gate_id in gate_ids:
                item = QListWidgetItem(library.spec(gate_id).label)
                item.setData(_GATE_ID_ROLE, gate_id)
                self.gate_list.addItem(item)
        self.select_gate(builtin_ids[0])

    def _add_heading(self, text: str, bold: bool = True) -> None:
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        font = QFont(self.gate_list.font())
        font.setBold(bold)
        item.setFont(font)
        self.gate_list.addItem(item)

    def _selected_gate(self) -> str | None:
        item = self.gate_list.currentItem()
        return None if item is None else item.data(_GATE_ID_ROLE)

    def _show_selected(self) -> None:
        gate_id = self._selected_gate()
        if gate_id is None:
            return
        library = self._session.library
        spec = library.spec(gate_id)
        self.title.setText(spec.label)
        self.description.setText(spec.description)
        self.wires.setText(f"Wires: {_numbered_wires(spec.wire_roles)}")
        self._show_symbol(gate_id, spec.wire_count)
        self._show_matrix(gate_id, spec.wire_count)
        self._show_usage(gate_id)

    def _show_symbol(self, gate_id: str, wire_count: int) -> None:
        self.preview.render_circuit(
            n_qubits=wire_count, gates=[PlacedGate(0, gate_id, tuple(range(wire_count)))],
        )
        column_end = (self.preview.cell_center(0, 0).x() + self.preview.cell_center(1, 0).x()) / 2
        bottom = self.preview.cell_center(0, wire_count).y()
        self.preview.setFixedSize(round(column_end) + _PREVIEW_MARGIN, round(bottom))

    def _show_matrix(self, gate_id: str, wire_count: int) -> None:
        size = 2**wire_count
        too_large = wire_count > _MAX_SHOWN_MATRIX_WIRES
        self.matrix_note.setVisible(too_large)
        self.matrix.setHidden(too_large)
        self.matrix.clear()
        if too_large:
            # The matrix is never built, so a large gate cannot exhaust memory.
            self.matrix_note.setText(f"The {size}×{size} matrix is too large to show.")
            self.matrix.setRowCount(0)
            self.matrix.setColumnCount(0)
            return

        matrix = self._session.library.matrix(gate_id)
        labels = [f"|{index:0{wire_count}b}⟩" for index in range(size)]
        self.matrix.setRowCount(size)
        self.matrix.setColumnCount(size)
        self.matrix.setHorizontalHeaderLabels(labels)
        self.matrix.setVerticalHeaderLabels(labels)
        for row in range(size):
            for column in range(size):
                item = QTableWidgetItem(format_complex(complex(matrix[row, column])))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.matrix.setItem(row, column, item)
        self.matrix.resizeColumnsToContents()

    def _show_usage(self, gate_id: str) -> None:
        placements = sum(gate.name == gate_id for gate in self._session.gates)
        usage = [f"Placed {placements} time(s) in the circuit." if placements else "Not placed in the circuit."]
        dependents = self._session.library.dependents(gate_id)
        if dependents:
            usage.append(f"Used by {', '.join(dependents)}.")
        self.usage.setText(" ".join(usage))

        self.save_button.setEnabled(not self._session.library.is_builtin(gate_id))
        blocker = self._session.deletion_blocker(gate_id)
        self.delete_button.setEnabled(blocker is None)
        self.delete_reason.setText(blocker or "")

    def _delete_selected(self) -> None:
        gate_id = self._selected_gate()
        answer = QMessageBox.question(
            self, "Delete gate", f"Delete {gate_id}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._session.delete_gate(gate_id)
        self.gate_deleted.emit(gate_id)
        self._fill_list()

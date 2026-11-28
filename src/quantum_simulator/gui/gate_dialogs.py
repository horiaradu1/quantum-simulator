"""Dialogs that define a gate from a matrix, by adding a control to an existing gate, or from the circuit.

Each dialog keeps a fixed checklist below its inputs. Every check shows its result while the
user types, and Create and Create and save… are enabled only when all of them pass.
"""

import cmath
from collections.abc import Callable, Iterable, Sequence
from html import escape

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..backend.expressions import format_complex, parse_complex
from ..backend.gate_library import (
    MAX_MATRIX_WIRES,
    CircuitGate,
    ControlledGate,
    GateDefinition,
    GateLibrary,
    MatrixGate,
)
from ..backend.gates import unitary_matrix
from .arrow_spin_box import ArrowSpinBox

type SaveGate = Callable[[GateDefinition], Iterable[GateDefinition] | None]

_MAX_NAME_LENGTH = 8
_WIRE_COUNT_WIDTH = 64
_MIN_DIALOG_WIDTH = 560
_PASSED, _FAILED, _NOT_CHECKED = "✓", "✗", "–"
_MARK_COLORS = {_PASSED: "#2e7d32", _FAILED: "#c62828", _NOT_CHECKED: "#8a8198"}
_UNREADABLE_CELL_STYLE = "border: 1px solid #c62828; border-radius: 3px;"
_CELL_WIDTH = 96
_REFERENCE_COLOR = "#60576f"

# Everything a matrix cell accepts, with examples. The dialog evaluates each example,
# so the values it shows always match what the parser does.
_CELL_INPUTS = (
    ("Numbers", ("1", "-0.5", "2.5e-3")),
    ("Imaginary unit (i or j)", ("i", "-i", "0.5i", "2-3i")),
    ("+  -  *  /  and brackets", ("1+i", "2*i", "1/2", "(1+i)/2")),
    ("Powers (^ or **)", ("1^2", "2**0.5", "i^2")),
    ("Constants", ("pi", "e")),
    ("Square root", ("sqrt(2)", "1/sqrt(2)", "sqrt(-1)")),
    ("Exponential", ("exp(i*pi/4)", "e^(i*pi)")),
    # Rotation gates such as Rx(θ) are written with cos(θ/2) and -i*sin(θ/2).
    ("Cosine and sine", ("sin(pi/2)", "cos(pi/8)", "-i*sin(pi/8)")),
)


def _example(text: str) -> str:
    """An example input in bold, followed by its value when that differs from the text."""
    value = format_complex(parse_complex(text))
    example = f'<span style="color: #382967; font-weight: 600;">{escape(text)}</span>'
    return example if value == text else f"{example} = {escape(value)}"


def _input_reference() -> QWidget:
    """List every kind of cell input with evaluated examples."""
    reference = QWidget()
    layout = QGridLayout(reference)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(16)
    layout.setVerticalSpacing(2)
    layout.setColumnStretch(1, 1)
    for row, (kind, examples) in enumerate(_CELL_INPUTS):
        kind_label = QLabel(kind)
        kind_label.setStyleSheet(f"color: {_REFERENCE_COLOR};")
        layout.addWidget(kind_label, row, 0)
        layout.addWidget(QLabel(",&nbsp;&nbsp; ".join(_example(text) for text in examples)), row, 1)

    notes = (
        "Spaces are ignored. Other names and functions, such as tan or log, are not accepted.",
        "The value of each expression is shown under its cell.",
    )
    for offset, note in enumerate(notes):
        note_label = QLabel(note)
        note_label.setStyleSheet(f"color: {_REFERENCE_COLOR};")
        layout.addWidget(note_label, len(_CELL_INPUTS) + offset, 0, 1, 2)
    return reference


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet("font-weight: 600;")
    return label


class Checklist(QWidget):
    """Rows that each show a mark, a title and a short detail, always in the same place."""

    def __init__(self, titles: Sequence[str]):
        super().__init__()
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnStretch(2, 1)
        self._marks: dict[str, QLabel] = {}
        self.details: dict[str, QLabel] = {}
        for row, title in enumerate(titles):
            mark = QLabel(_NOT_CHECKED)
            mark.setFixedWidth(16)
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: 600;")
            detail = QLabel()
            detail.setWordWrap(True)
            detail.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            # Two lines are reserved, so a longer message never moves the rows below it.
            detail.setFixedHeight(2 * detail.fontMetrics().lineSpacing())
            layout.addWidget(mark, row, 0, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(title_label, row, 1, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(detail, row, 2)
            self._marks[title] = mark
            self.details[title] = detail

    def set_result(self, title: str, passed: bool | None, detail: str) -> None:
        """Show a check as passed, failed, or not checked yet (None)."""
        mark = {True: _PASSED, False: _FAILED, None: _NOT_CHECKED}[passed]
        self._marks[title].setText(mark)
        self._marks[title].setStyleSheet(f"color: {_MARK_COLORS[mark]}; font-weight: 700;")
        self.details[title].setText(detail)


class _DefinitionDialog(QDialog):
    """Shared parts: a name, a checklist, and Create, Create and save… and Cancel.

    Both create buttons are enabled only for a valid definition. Create and save… calls save_gate,
    which asks where to save and writes the file. It returns the definitions it wrote, or None if
    the user cancels or the write fails, and then the dialog stays open with the user's input.
    """

    def __init__(
        self, title: str, library: GateLibrary, check_titles: Sequence[str], parent: QWidget | None,
        save_gate: SaveGate | None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(_MIN_DIALOG_WIDTH)
        self._library = library
        self._definition: GateDefinition | None = None
        self._save_gate = save_gate

        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(_MAX_NAME_LENGTH)
        self.form = QFormLayout()
        self.form.addRow("&Name", self.name_edit)
        self.checks = Checklist(check_titles)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create")
        self.save_button = self.buttons.addButton("Create and save…", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_button.setVisible(save_gate is not None)
        self.save_button.clicked.connect(self._create_and_save)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def definition(self) -> GateDefinition:
        """The checked definition. Only valid after the dialog was accepted."""
        return self._definition

    def _create_and_save(self) -> None:
        written = self._save_gate(self._definition)
        if written:
            self.accept()

    def _add_creation_choices(self, layout: QVBoxLayout) -> None:
        message = (
            "Create adds the gate to the palette. Save a circuit that uses it to keep it, "
            "or save it separately later with Manage gates → Save gate as…"
        )
        if self._save_gate is not None:
            message += "\nCreate and save… also saves the gate to its own file now."
        hint = QLabel(message)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addWidget(self.buttons)

    def _check_name(self) -> bool:
        name = self.name_edit.text()
        if not name:
            self.checks.set_result("Name", False, "Enter a name for the new gate.")
            return False
        try:
            self._library.check_name(name)
        except ValueError as error:
            self.checks.set_result("Name", False, str(error))
            return False
        self.checks.set_result("Name", True, f"{name} is available.")
        return True

    def _set_definition(self, definition: GateDefinition | None) -> None:
        self._definition = definition
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(definition is not None)
        self.save_button.setEnabled(definition is not None)


class MatrixGateDialog(_DefinitionDialog):
    """Let the user name a unitary matrix and see every problem with it while they type."""

    def __init__(
        self, library: GateLibrary, parent: QWidget | None = None, save_gate: SaveGate | None = None
    ):
        super().__init__("New matrix gate", library, ("Name", "Entries", "Unitary"), parent, save_gate)
        self.cells: list[list[QLineEdit]] = []
        self.cell_values: list[list[QLabel]] = []

        self.wire_count = ArrowSpinBox()
        self.wire_count.setRange(1, MAX_MATRIX_WIRES)
        self.wire_count.setFixedWidth(_WIRE_COUNT_WIDTH)
        self.form.addRow("&Wires", self.wire_count)
        self._grid = QGridLayout()
        self._grid.setSpacing(4)

        self.reference_toggle = QToolButton()
        self.reference_toggle.setText("What a cell accepts")
        self.reference_toggle.setAutoRaise(True)
        self.reference_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.reference_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.reference = _input_reference()
        self.reference.hide()

        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addSpacing(4)
        layout.addWidget(self.reference_toggle, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.reference)
        layout.addSpacing(8)
        layout.addWidget(_section_label("Matrix: columns are input states, rows are output states"))
        layout.addLayout(self._grid)
        layout.addSpacing(8)
        layout.addWidget(self.checks)
        layout.addStretch()
        self._add_creation_choices(layout)

        self.reference_toggle.clicked.connect(self._toggle_reference)
        self.name_edit.textChanged.connect(self._check)
        self.wire_count.valueChanged.connect(self._build_cells)
        self._build_cells(self.wire_count.value())

    def _toggle_reference(self) -> None:
        shown = self.reference.isHidden()
        self.reference.setVisible(shown)
        self.reference_toggle.setArrowType(Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow)

    def _build_cells(self, wire_count: int) -> None:
        while self._grid.count():
            old_widget = self._grid.takeAt(0).widget()
            old_widget.hide()
            old_widget.deleteLater()

        size = 2**wire_count
        labels = [f"|{index:0{wire_count}b}⟩" for index in range(size)]
        for position, label in enumerate(labels):
            self._grid.addWidget(QLabel(label), 0, position + 1, Qt.AlignmentFlag.AlignCenter)

        # Each matrix row takes two grid rows: the cells, then the values of their expressions.
        # Start from the identity so a new gate begins as a valid matrix.
        self.cells = []
        self.cell_values = []
        for row in range(size):
            cell_row = 2 * row + 1
            self._grid.addWidget(QLabel(labels[row]), cell_row, 0)
            row_cells = []
            row_values = []
            for column in range(size):
                cell = QLineEdit("1" if row == column else "0")
                cell.setMinimumWidth(_CELL_WIDTH)
                cell.textChanged.connect(self._check)
                value = self._value_label()
                self._grid.addWidget(cell, cell_row, column + 1)
                self._grid.addWidget(value, cell_row + 1, column + 1)
                row_cells.append(cell)
                row_values.append(value)
            self.cells.append(row_cells)
            self.cell_values.append(row_values)
        self._check()

    @staticmethod
    def _value_label() -> QLabel:
        label = QLabel()
        label.setStyleSheet("color: #60576f;")
        font = label.font()
        font.setPointSize(font.pointSize() - 1)
        label.setFont(font)
        label.setFixedHeight(label.fontMetrics().lineSpacing())
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        return label

    def _check(self) -> None:
        name_is_valid = self._check_name()
        entries = self._read_cells()
        is_unitary = self._check_unitary(entries)

        definition = None
        if name_is_valid and entries is not None and is_unitary:
            definition = MatrixGate(self.name_edit.text(), entries)
        self._set_definition(definition)

    def _read_cells(self) -> list[list[complex]] | None:
        """Read every cell, outline the unreadable ones, and return the entries if all can be read."""
        entries = []
        unreadable_count = 0
        for row_cells, row_values in zip(self.cells, self.cell_values):
            values = []
            for cell, value_label in zip(row_cells, row_values):
                try:
                    value = parse_complex(cell.text())
                    if not cmath.isfinite(value):
                        raise ValueError("The value is not finite.")
                except ValueError as error:
                    unreadable_count += 1
                    cell.setStyleSheet(_UNREADABLE_CELL_STYLE)
                    cell.setToolTip(str(error))
                    value_label.clear()
                    value = None
                else:
                    cell.setStyleSheet("")
                    cell.setToolTip("")
                    shown_value = format_complex(value)
                    value_label.setText("" if shown_value == cell.text().strip() else f"= {shown_value}")
                bold = value is not None and value != 0
                for widget in (cell, value_label):
                    font = widget.font()
                    if font.bold() != bold:
                        font.setBold(bold)
                        widget.setFont(font)
                values.append(value)
            entries.append(values)

        cell_count = len(self.cells) ** 2
        if unreadable_count:
            self.checks.set_result(
                "Entries", False,
                f"{unreadable_count} of {cell_count} entries cannot be read. "
                "They are outlined in red; hover over one to see why.",
            )
            return None
        self.checks.set_result("Entries", True, f"All {cell_count} entries are numbers.")
        return entries

    def _check_unitary(self, entries: list[list[complex]] | None) -> bool:
        if entries is None:
            self.checks.set_result("Unitary", None, "Checked once every entry can be read.")
            return False

        matrix = np.array(entries, dtype=np.complex128)
        try:
            stored_matrix = unitary_matrix(matrix, self.wire_count.value())
        except ValueError:
            self.checks.set_result("Unitary", False, "The matrix is not unitary, so it cannot be a gate.")
            return False

        if np.array_equal(stored_matrix, matrix):
            detail = "The matrix is unitary."
        else:
            detail = "Close enough to unitary. It will be stored as the nearest exact unitary."
        self.checks.set_result("Unitary", True, detail)
        return True


class ControlledGateDialog(_DefinitionDialog):
    """Let the user add one control wire before the wires of an existing gate."""

    def __init__(
        self, library: GateLibrary, parent: QWidget | None = None, save_gate: SaveGate | None = None
    ):
        super().__init__("New controlled gate", library, ("Name", "Wires"), parent, save_gate)
        self.base_choice = QComboBox()
        self.base_choice.addItems(library.gate_ids())
        self.form.insertRow(0, "&Control", self.base_choice)

        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addSpacing(8)
        layout.addWidget(self.checks)
        self._add_creation_choices(layout)

        self.base_choice.currentTextChanged.connect(self._suggest_name)
        self.name_edit.textChanged.connect(self._check)
        self._suggest_name(self.base_choice.currentText())

    def _suggest_name(self, base: str) -> None:
        self.name_edit.setText(f"C{base}"[:_MAX_NAME_LENGTH])
        self._check()

    def _check(self) -> None:
        base = self.base_choice.currentText()
        base_wires = self._library.spec(base).wire_count
        base_wires_text = "1 wire" if base_wires == 1 else f"{base_wires} wires"
        self.checks.set_result(
            "Wires", True,
            f"{base_wires + 1} wires in total: one control, then the {base_wires_text} of {base}.",
        )

        definition = None
        if self._check_name():
            definition = ControlledGate(self.name_edit.text(), base, base_wires + 1)
        self._set_definition(definition)


class CircuitGateDialog(_DefinitionDialog):
    """Name a gate made from the open circuit, then create it, or create it and save it to a file."""

    def __init__(
        self, library: GateLibrary, make_gate: Callable[[str], CircuitGate], wire_count: int,
        parent: QWidget | None = None, save_gate: SaveGate | None = None,
    ):
        super().__init__("Define gate from circuit", library, ("Name",), parent, save_gate)
        self._make_gate = make_gate
        wires = "1 wire" if wire_count == 1 else f"{wire_count} wires"
        summary = QLabel(f"A gate on {wires} that applies the circuit's gates in order.")

        layout = QVBoxLayout(self)
        layout.addWidget(summary)
        layout.addLayout(self.form)
        layout.addSpacing(8)
        layout.addWidget(self.checks)
        self._add_creation_choices(layout)

        self.name_edit.textChanged.connect(self._check)
        self._check()

    def _check(self) -> None:
        definition = None
        if self._check_name():
            definition = self._make_gate(self.name_edit.text())
        self._set_definition(definition)

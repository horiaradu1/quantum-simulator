"""Connect the desktop circuit editor to the simulator. Run main() to open the window."""

import sys
from collections.abc import Iterator
from functools import partial
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from time import perf_counter

from PySide6.QtCore import QSignalBlocker, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QFontDatabase, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..backend import Outcome, QuantumState
from ..backend.circuit import MAX_QUBITS
from ..backend.circuit_file import SAVED_CIRCUITS, load_circuit, save_circuit, saved_circuit_path, shared_circuits
from ..backend.editor import EditorSession, Placement
from ..backend.gate_library import GateDefinition
from .arrow_spin_box import ArrowSpinBox
from .basis_state_spin_box import BasisStateSpinBox
from .circuit_view import CircuitView
from .flow_layout import FlowLayout
from .gate_dialogs import ControlledGateDialog, MatrixGateDialog
from .gate_manager import GateManagerDialog
from .gate_button import GateButton
from .styles import WINDOW_STYLE

_DISPLAY_TOLERANCE = 1e-12
_LOGO_PATH = files("quantum_simulator") / "resources" / "images" / "MScQCLogo.png"
_LOGO_HEIGHT = 44
_MINIMUM_SIZE = QSize(720, 560)
_DESIGN_SIZE = QSize(1000, 720)
_SCREEN_FRACTION = 0.8


def _panel() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 11, 14, 11)
    layout.setSpacing(8)
    return frame, layout


def _section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


class SimulatorWindow(QMainWindow):
    """Forward edits to the editor session, run the circuit, and display or measure its final state."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quantum Simulator")
        self.setMinimumSize(_MINIMUM_SIZE)
        self._fit_to_screen()
        self.setStyleSheet(WINDOW_STYLE)

        self.session = EditorSession(qubits=2)
        self.saved_circuits = SAVED_CIRCUITS
        self._run_steps: Iterator[None] | None = None
        self._run_timer = QTimer(self)
        self._run_timer.timeout.connect(self._advance_run)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.pages.addWidget(root)
        self.loading_screen = self._build_loading_screen()
        self.pages.addWidget(self.loading_screen)
        self._build_menu()
        layout.addWidget(self._build_controls())

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.addWidget(self._build_circuit())
        splitter.addWidget(self._build_results())
        splitter.setSizes([340, 210])
        layout.addWidget(splitter, 1)
        self.logo = self._build_logo()
        layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignRight)

        self.qubit_count.valueChanged.connect(self._change_qubits)
        self.initial_state.valueChanged.connect(self._edit_initial_state)
        self.initial_state.lineEdit().textChanged.connect(self._edit_initial_state)
        self.initial_state.editingFinished.connect(self._update_run_availability)
        self._change_qubits(self.qubit_count.value())

    def _build_loading_screen(self) -> QFrame:
        frame, layout = _panel()
        layout.addStretch()
        title = _section_title("Spooky action at a distance in progress…")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
        message = QLabel("Please wait while the qubits compare notes.")
        layout.addWidget(message, 0, Qt.AlignmentFlag.AlignCenter)
        progress = QProgressBar()
        progress.setAccessibleName("Simulation in progress")
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.setFixedSize(240, 10)
        layout.addWidget(progress, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return frame

    def _fit_to_screen(self) -> None:
        """Open centred and scaled to the screen, but never below the minimum size."""
        available = self.screen().availableGeometry()
        # The screen's tighter dimension sets the scale, so an ultrawide screen does not
        # stretch the window sideways.
        width_scale = available.width() / _DESIGN_SIZE.width()
        height_scale = available.height() / _DESIGN_SIZE.height()
        scale = _SCREEN_FRACTION * min(width_scale, height_scale)
        width = max(_MINIMUM_SIZE.width(), round(_DESIGN_SIZE.width() * scale))
        height = max(_MINIMUM_SIZE.height(), round(_DESIGN_SIZE.height() * scale))
        self.resize(width, height)

        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        self.open_action = file_menu.addAction("&Open…")
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self._choose_circuit_file)
        self.save_action = file_menu.addAction("&Save…")
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self._save_circuit)

        gates_menu = self.menuBar().addMenu("&Gates")
        self.new_matrix_gate_action = gates_menu.addAction("New &matrix gate…")
        self.new_matrix_gate_action.triggered.connect(self._define_matrix_gate)
        self.new_controlled_gate_action = gates_menu.addAction("New &controlled gate…")
        self.new_controlled_gate_action.triggered.connect(self._define_controlled_gate)
        gates_menu.addSeparator()
        self.manage_gates_action = gates_menu.addAction("Manage &gates…")
        self.manage_gates_action.triggered.connect(self._manage_gates)

        self.examples_menu = file_menu.addMenu("&Examples")
        for name, path in shared_circuits().items():
            action = self.examples_menu.addAction(name)
            action.triggered.connect(partial(self._open_circuit, path))

    def _build_controls(self) -> QFrame:
        frame, layout = _panel()
        layout.addLayout(self._build_settings_row())
        layout.addLayout(self._build_gate_palette())
        return frame

    def _build_settings_row(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.qubit_count = ArrowSpinBox()
        self.qubit_count.setObjectName("qubitCount")
        # Accept any typed count, so a count above MAX_QUBITS shows an error instead of being ignored.
        self.qubit_count.setRange(1, 2**31 - 1)
        self.qubit_count.setValue(2)
        self.qubit_count.setMinimumSize(64, 30)
        # Typing 12 should not pass through 1 on the way, which would ask to remove gates.
        self.qubit_count.setKeyboardTracking(False)
        qubits_label = QLabel("&Qubits")
        qubits_label.setBuddy(self.qubit_count)
        controls.addWidget(qubits_label)
        controls.addWidget(self.qubit_count)
        controls.addSpacing(8)

        self.initial_state = BasisStateSpinBox()
        self.initial_state.setObjectName("initialState")
        self.initial_state.setMinimumWidth(115)
        self.initial_state.setMinimumHeight(30)
        initial_label = QLabel("&Initial state")
        initial_label.setBuddy(self.initial_state)
        controls.addWidget(initial_label)
        controls.addWidget(self.initial_state)
        controls.addStretch()

        self.run_button = QPushButton("&Run")
        self.run_button.setObjectName("runButton")
        self.run_button.setMinimumWidth(90)
        self.run_button.clicked.connect(self._run)
        controls.addWidget(self.run_button)
        self.measure_button = QPushButton("&Measure")
        self.measure_button.setMinimumWidth(90)
        self.measure_button.clicked.connect(self._measure)
        controls.addWidget(self.measure_button)
        return controls

    def _build_gate_palette(self) -> QHBoxLayout:
        palette = QHBoxLayout()
        palette.setSpacing(6)
        title = _section_title("Gates")
        palette.addWidget(title, 0, Qt.AlignmentFlag.AlignTop)
        palette.addSpacing(6)

        # Buttons wrap onto more rows so every gate stays reachable at the minimum width.
        self._gate_button_layout = FlowLayout()
        self._gate_button_layout.setSpacing(6)
        self._gate_button_group = QButtonGroup(self)
        self.gate_buttons: dict[str, GateButton] = {}
        self._add_missing_gate_buttons()
        self.gate_buttons[self.session.selected_gate].setChecked(True)
        palette.addLayout(self._gate_button_layout, 1)
        return palette

    def _add_missing_gate_buttons(self) -> None:
        for gate_id in self.session.library.gate_ids():
            if gate_id in self.gate_buttons:
                continue
            button = GateButton(gate_id, self.session.library.spec(gate_id).label)
            button.setCheckable(True)
            button.clicked.connect(partial(self._select_gate, gate_id))
            self._gate_button_group.addButton(button)
            self._gate_button_layout.addWidget(button)
            self.gate_buttons[gate_id] = button

    def _build_circuit(self) -> QFrame:
        frame, layout = _panel()
        heading = QHBoxLayout()
        heading.addWidget(_section_title("Circuit"))
        heading.addStretch()
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_circuit)
        heading.addWidget(self.clear_button)
        layout.addLayout(heading)

        self.circuit_view = CircuitView(library=self.session.library)
        self.circuit_view.gate_dropped.connect(self._drop_gate)
        self.circuit_view.cell_clicked.connect(self._place_gate)
        self.circuit_view.cell_removed.connect(self._remove_gate)
        layout.addWidget(self.circuit_view, 1)
        self.circuit_hint = QLabel()
        self.circuit_hint.setObjectName("hint")
        layout.addWidget(self.circuit_hint)
        return frame

    def _build_results(self) -> QFrame:
        frame, layout = _panel()
        heading = QHBoxLayout()
        heading.addWidget(_section_title("Results"))
        heading.addStretch()
        self.result_summary = QLabel()
        self.result_summary.setObjectName("hint")
        heading.addWidget(self.result_summary)
        layout.addLayout(heading)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Basis", "Amplitude", "Probability"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.verticalHeader().hide()
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)
        if sys.platform == "win32":
            font.setFamily("Consolas")
        self.results_table.setFont(font)
        layout.addWidget(self.results_table, 1)
        return frame

    def _build_logo(self) -> QToolButton:
        logo = QToolButton()
        logo.setAutoRaise(True)
        logo.setAccessibleName("Open the MSc Quantum Computing website")
        logo.setCursor(Qt.CursorShape.PointingHandCursor)
        website = QUrl("https://quantum.upb.ro/")
        logo.setToolTip(website.toDisplayString())
        logo.clicked.connect(lambda: QDesktopServices.openUrl(website))
        # Scale to device pixels so the logo stays sharp on high-DPI screens.
        ratio = self.devicePixelRatioF()
        pixmap = QPixmap(str(_LOGO_PATH)).scaledToHeight(
            round(_LOGO_HEIGHT * ratio), Qt.TransformationMode.SmoothTransformation
        )
        pixmap.setDevicePixelRatio(ratio)
        logo.setIcon(QIcon(pixmap))
        logo.setIconSize(pixmap.deviceIndependentSize().toSize())
        return logo

    def _change_qubits(self, count: int) -> None:
        if count > MAX_QUBITS:
            QMessageBox.warning(self, "Too many qubits", "Please dont ruin my memory .... :(")
            self._restore_qubit_count()
            return
        removes_gates = bool(self.session.gates_removed_by(count))
        if removes_gates and not self._confirm_gate_removal(count):
            self._restore_qubit_count()
            return

        with QSignalBlocker(self.initial_state), QSignalBlocker(self.initial_state.lineEdit()):
            self.initial_state.set_qubit_count(count)

        self.session.set_qubit_count(count)
        self._update_gate_buttons()
        self._refresh_circuit()
        self._invalidate_results()

    def _restore_qubit_count(self) -> None:
        with QSignalBlocker(self.qubit_count):
            self.qubit_count.setValue(self.session.qubits)

    def _confirm_gate_removal(self, count: int) -> bool:
        answer = QMessageBox.question(
            self, "Remove gates",
            f"Lowering to {count} qubits removes the gates on the removed wires. Continue?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Ok

    def _edit_initial_state(self) -> None:
        self.session.modified = True
        self._invalidate_results()

    def _update_gate_buttons(self) -> None:
        for gate_id, button in self.gate_buttons.items():
            button.setEnabled(self.session.fits(gate_id))
        self.gate_buttons[self.session.selected_gate].setChecked(True)

    def _save_circuit(self) -> bool:
        """Ask for a name and save the circuit. Return whether it was saved."""
        if not self.initial_state.hasAcceptableInput():
            QMessageBox.warning(self, "Save circuit", "Enter a complete initial state before saving.")
            return False
        name, accepted = QInputDialog.getText(self, "Save circuit", "Circuit name:")
        if not accepted:
            return False
        try:
            path = saved_circuit_path(name, self.saved_circuits)
        except ValueError as error:
            QMessageBox.warning(self, "Save circuit", str(error))
            return False
        if path.exists():
            answer = QMessageBox.question(self, "Save circuit", f"Replace the saved circuit {path.stem}?")
            if answer != QMessageBox.StandardButton.Yes:
                return False

        circuit = self.session.circuit(self.initial_state.text())
        try:
            save_circuit(path, circuit, self.session.settings)
        except OSError as error:
            QMessageBox.warning(self, "Save circuit", f"Could not save {path.name}: {error.strerror or error}.")
            return False
        self.session.modified = False
        return True

    def _confirm_discard(self, action: str) -> bool:
        """Offer to save unsaved changes before an action replaces them. Return whether to go ahead."""
        if not self.session.modified:
            return True
        answer = QMessageBox.question(
            self, "Unsaved changes", f"The circuit has unsaved changes. Save them before {action}?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self._save_circuit()
        return answer == QMessageBox.StandardButton.Discard

    def _choose_circuit_file(self) -> None:
        self.saved_circuits.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self, "Open circuit", str(self.saved_circuits), "Circuit files (*.json)"
        )
        if path:
            self._open_circuit(Path(path))

    def _open_circuit(self, path: Traversable) -> None:
        if not self._confirm_discard("opening another circuit"):
            return
        # Loading the session first means a rejected file or gate name changes nothing.
        try:
            circuit, settings = load_circuit(path)
            self.session.load(circuit, settings)
        except ValueError as error:
            QMessageBox.warning(self, "Open circuit", str(error))
            return

        with QSignalBlocker(self.qubit_count):
            self.qubit_count.setValue(circuit.qubits)
        with QSignalBlocker(self.initial_state), QSignalBlocker(self.initial_state.lineEdit()):
            self.initial_state.set_qubit_count(circuit.qubits)
            self.initial_state.setValue(int(circuit.initial_bits, 2))
        self._add_missing_gate_buttons()
        self._update_gate_buttons()
        self._refresh_circuit()
        self._invalidate_results()

    def _define_matrix_gate(self) -> None:
        dialog = MatrixGateDialog(self.session.library, self)
        if dialog.exec():
            self._add_definition(dialog.definition())

    def _define_controlled_gate(self) -> None:
        dialog = ControlledGateDialog(self.session.library, self)
        if dialog.exec():
            self._add_definition(dialog.definition())

    def _manage_gates(self) -> None:
        dialog = GateManagerDialog(self.session, self)
        dialog.gate_deleted.connect(self._remove_gate_button)
        dialog.exec()

    def _remove_gate_button(self, gate_id: str) -> None:
        button = self.gate_buttons.pop(gate_id)
        self._gate_button_group.removeButton(button)
        self._gate_button_layout.removeWidget(button)
        button.hide()
        button.deleteLater()
        self._update_gate_buttons()
        self._refresh_circuit()

    def _add_definition(self, definition: GateDefinition) -> None:
        self.session.library.add(definition)
        self._add_missing_gate_buttons()
        self._update_gate_buttons()
        if self.session.fits(definition.gate_id):
            self._select_gate(definition.gate_id)

    def _select_gate(self, gate_id: str) -> None:
        self.session.select_gate(gate_id)
        self.gate_buttons[gate_id].setChecked(True)
        self._refresh_circuit()

    def _drop_gate(self, gate_id: str, step: int, wire: int) -> None:
        button = self.gate_buttons.get(gate_id)
        if button is None or not button.isEnabled():
            return
        if gate_id != self.session.selected_gate:
            self._select_gate(gate_id)
        self._place_gate(step, wire)

    def _refresh_circuit(self) -> None:
        session = self.session
        self.circuit_view.render_circuit(
            n_qubits=session.qubits,
            gates=session.gates,
            column_count=session.column_count,
            pending_step=session.pending_step,
            pending_wires=session.pending_wires,
        )
        self.clear_button.setEnabled(bool(session.gates or session.pending_wires))
        role = session.pending_role
        if role is None:
            self.circuit_hint.setText("Drag gates onto wires. Right-click a gate to remove it.")
        else:
            # The canvas highlights the gate's column, so the hint only names the wire to choose.
            self.circuit_hint.setText(f"Choose the {role}.")

    def _place_gate(self, step: int, wire: int) -> None:
        placement = self.session.place(step, wire)
        self._refresh_circuit()
        if placement is Placement.REPEATED_WIRE:
            self.circuit_hint.setText("Choose a different wire.")
        elif placement is Placement.BLOCKED:
            self.circuit_hint.setText("A gate already crosses these wires.")
        elif placement is Placement.PLACED:
            self._invalidate_results()

    def _remove_gate(self, step: int, wire: int) -> None:
        removed = self.session.remove_at(step, wire)
        self._refresh_circuit()
        if removed:
            self._invalidate_results()

    def _clear_circuit(self) -> None:
        if not self._confirm_discard("clearing it"):
            return
        self.session.clear()
        self._refresh_circuit()
        self._invalidate_results()

    def _invalidate_results(self) -> None:
        if self._run_steps is not None:
            self._finish_run()
        self.session.invalidate_result()
        self.measure_button.setEnabled(False)
        self.results_table.setRowCount(0)
        self._update_run_availability()

    def _update_run_availability(self) -> None:
        valid_basis = self.initial_state.hasAcceptableInput()
        self.run_button.setEnabled(valid_basis)
        if self.session.result is not None:
            return
        if valid_basis:
            self.result_summary.setText("Run the circuit to see results.")
        else:
            count = self.qubit_count.value()
            self.result_summary.setText(f"Enter {count} {'bit' if count == 1 else 'bits'} (0 or 1).")

    def _run(self) -> None:
        if self._run_steps is not None or not self.initial_state.hasAcceptableInput():
            return
        # A gate still waiting for wires is not part of the circuit, so drop it.
        if self.session.pending_wires:
            self.session.reset_placement()
            self._refresh_circuit()
        self._invalidate_results()
        self._run_steps = self._simulate(self.initial_state.text())
        self.pages.setCurrentWidget(self.loading_screen)
        self._run_timer.start(1)

    def _advance_run(self) -> None:
        if self._run_steps is None:
            return
        # Return to Qt between batches so loading, resizing and closing stay responsive.
        deadline = perf_counter() + 0.008
        try:
            while perf_counter() < deadline:
                next(self._run_steps)
        except StopIteration:
            self._finish_run()
        except Exception as error:
            self._finish_run()
            self._invalidate_results()
            self.result_summary.setText(f"Simulation failed: {error}")

    def _finish_run(self) -> None:
        self._run_timer.stop()
        self._run_steps = None
        self.pages.setCurrentIndex(0)

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._confirm_discard("closing"):
            event.ignore()
            return
        if self._run_steps is not None:
            self._invalidate_results()
        super().closeEvent(event)

    def _simulate(self, basis: str) -> Iterator[None]:
        yield from self.session.run_steps(basis)
        yield from self._display_results(self.session.result)
        self.measure_button.setEnabled(True)

    def _display_results(self, state: QuantumState) -> Iterator[None]:
        outcome_count = 0
        self.results_table.setRowCount(2**state.n_qubits)
        for outcome in state.outcomes():
            # Treat tiny rounding residues as zero when displaying the state.
            if outcome.magnitude > _DISPLAY_TOLERANCE:
                self._set_outcome_row(outcome_count, outcome)
                outcome_count += 1
            yield
        self.results_table.setRowCount(outcome_count)
        label = "outcome" if outcome_count == 1 else "outcomes"
        self.result_summary.setText(f"{outcome_count} nonzero {label}")

    def _measure(self) -> None:
        if self.session.result is None:
            return

        basis = self.session.result.measure()
        self.results_table.setRowCount(1)
        self._set_outcome_row(0, Outcome(basis, 1 + 0j, 1.0))
        self.result_summary.setText(f"Measured |{basis}⟩")

    def _set_outcome_row(self, row: int, outcome: Outcome) -> None:
        amplitude = outcome.amplitude
        amplitude_text = f"{amplitude.real:.4f}"
        if abs(amplitude.imag) >= _DISPLAY_TOLERANCE:
            amplitude_text += f"{amplitude.imag:+.4f}i"
        values = (outcome.basis, amplitude_text, f"{outcome.probability:.2%}")
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, column, item)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Quantum Simulator")
    # The stylesheet only defines light colors. A dark system theme would otherwise
    # give menus and dialogs dark backgrounds behind the stylesheet's dark text.
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    font = app.font()
    font.setPointSize(10)
    if sys.platform == "win32":
        font.setFamily("Segoe UI")
    app.setFont(font)
    window = SimulatorWindow()
    window.show()
    return app.exec()

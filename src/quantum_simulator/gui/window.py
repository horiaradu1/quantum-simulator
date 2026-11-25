"""Connect the desktop circuit editor to the simulator. Run main() to open the window."""

import sys
from collections.abc import Iterator
from functools import partial
from time import perf_counter

from PySide6.QtCore import QSignalBlocker, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QFontDatabase
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..backend import Outcome, QuantumState
from .arrow_spin_box import ArrowSpinBox
from .basis_state_spin_box import BasisStateSpinBox
from .circuit_view import CircuitView, PlacedGate
from .gate_button import GateButton
from .styles import WINDOW_STYLE

_GATE_ROLES = {
    "H": ("target",),
    "X": ("target",),
    "Y": ("target",),
    "Z": ("target",),
    "S": ("target",),
    "T": ("target",),
    "CNOT": ("control", "target"),
    "CH": ("control", "target"),
    "SWAP": ("first wire", "second wire"),
    "TOFFOLI": ("first control", "second control", "target"),
}

_DISPLAY_TOLERANCE = 1e-12


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
    """Manage gate placement, run the circuit, and display or measure its final state."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quantum Simulator")
        self.resize(1000, 720)
        self.setMinimumSize(720, 560)
        self.setStyleSheet(WINDOW_STYLE)

        self._gates: list[PlacedGate] = []
        self._selected_gate = "H"
        self._pending_step: int | None = None
        self._pending_wires: tuple[int, ...] = ()
        self._result_state: QuantumState | None = None
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
        layout.addWidget(self._build_controls())

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.addWidget(self._build_circuit())
        splitter.addWidget(self._build_results())
        splitter.setSizes([340, 210])
        layout.addWidget(splitter, 1)

        self.qubit_count.valueChanged.connect(self._change_qubits)
        self.initial_state.valueChanged.connect(self._invalidate_results)
        self.initial_state.lineEdit().textChanged.connect(self._invalidate_results)
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
        self.qubit_count.setRange(1, 12)
        self.qubit_count.setValue(2)
        self.qubit_count.setMinimumSize(64, 30)
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
        palette.addWidget(_section_title("Gates"))
        palette.addSpacing(6)
        group = QButtonGroup(self)
        self.gate_buttons: dict[str, GateButton] = {}
        for gate in _GATE_ROLES:
            button = GateButton(gate)
            button.setCheckable(True)
            button.clicked.connect(partial(self._select_gate, gate))
            group.addButton(button)
            palette.addWidget(button)
            self.gate_buttons[gate] = button
        self.gate_buttons[self._selected_gate].setChecked(True)
        palette.addStretch()
        return palette

    def _build_circuit(self) -> QFrame:
        frame, layout = _panel()
        heading = QHBoxLayout()
        heading.addWidget(_section_title("Circuit"))
        heading.addStretch()
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_circuit)
        heading.addWidget(self.clear_button)
        layout.addLayout(heading)

        self.circuit_view = CircuitView()
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

    def _change_qubits(self, count: int) -> None:
        with QSignalBlocker(self.initial_state), QSignalBlocker(self.initial_state.lineEdit()):
            self.initial_state.set_qubit_count(count)

        self._gates = [gate for gate in self._gates if max(gate.wires) < count]
        for name, button in self.gate_buttons.items():
            button.setEnabled(len(_GATE_ROLES[name]) <= count)
        if not self.gate_buttons[self._selected_gate].isEnabled():
            self._selected_gate = "H"
            self.gate_buttons["H"].setChecked(True)
        self._reset_placement()
        self._invalidate_results()

    def _select_gate(self, name: str) -> None:
        self._selected_gate = name
        self.gate_buttons[name].setChecked(True)
        self._reset_placement()

    def _drop_gate(self, name: str, step: int, wire: int) -> None:
        button = self.gate_buttons.get(name)
        if button is None or not button.isEnabled():
            return
        if name != self._selected_gate:
            self._select_gate(name)
        self._place_gate(step, wire)

    def _reset_placement(self) -> None:
        self._pending_step = None
        self._pending_wires = ()
        self._refresh_circuit()

    def _refresh_circuit(self) -> None:
        self.circuit_view.render_circuit(
            n_qubits=self.qubit_count.value(),
            gates=self._gates,
            pending_step=self._pending_step,
            pending_wires=self._pending_wires,
        )
        self.clear_button.setEnabled(bool(self._gates or self._pending_wires))
        if self._pending_step is None:
            self.circuit_hint.setText("Drag gates onto wires. Right-click a gate to remove it.")
        else:
            gate = self.gate_buttons[self._selected_gate].text()
            role = _GATE_ROLES[self._selected_gate][len(self._pending_wires)]
            step_number = self._pending_step + 1
            self.circuit_hint.setText(
                f"Choose the {role} in step {step_number}. Click a wire or drop {gate} again."
            )

    def _place_gate(self, step: int, wire: int) -> None:
        # Choosing another column starts a new gate at its first wire.
        if self._pending_step is not None and self._pending_step != step:
            self._reset_placement()

        if wire in self._pending_wires:
            self.circuit_hint.setText("Choose a different wire in this step.")
            return

        chosen_wires = self._pending_wires + (wire,)
        gate = PlacedGate(step, self._selected_gate, chosen_wires)
        if any(gate.overlaps(placed_gate) for placed_gate in self._gates):
            self.circuit_hint.setText("A gate already crosses these wires in this step.")
            return

        wire_roles = _GATE_ROLES[gate.name]
        if len(chosen_wires) < len(wire_roles):
            self._pending_step = step
            self._pending_wires = chosen_wires
            self._refresh_circuit()
            return

        self._gates.append(gate)
        self._reset_placement()
        self._invalidate_results()

    def _remove_gate(self, step: int, wire: int) -> None:
        for gate in self._gates:
            if gate.step == step and wire in gate.wire_span:
                self._gates.remove(gate)
                self._invalidate_results()
                break
        self._reset_placement()

    def _clear_circuit(self) -> None:
        self._gates.clear()
        self._reset_placement()
        self._invalidate_results()

    def _invalidate_results(self) -> None:
        self._result_state = None
        self.measure_button.setEnabled(False)
        self.results_table.setRowCount(0)
        self._update_run_availability()

    def _update_run_availability(self) -> None:
        valid_basis = self.initial_state.hasAcceptableInput()
        self.run_button.setEnabled(valid_basis)
        if self._result_state is not None:
            return
        if valid_basis:
            self.result_summary.setText("Run the circuit to see results.")
        else:
            count = self.qubit_count.value()
            self.result_summary.setText(f"Enter {count} {'bit' if count == 1 else 'bits'} (0 or 1).")

    def _run(self) -> None:
        if self._run_steps is not None or not self.initial_state.hasAcceptableInput():
            return
        if self._pending_wires:
            self._reset_placement()
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
        if self._run_steps is not None:
            self._finish_run()
            self._invalidate_results()
        super().closeEvent(event)

    def _simulate(self, basis: str) -> Iterator[None]:
        state = QuantumState(len(basis))
        state.initialize(basis)

        yield from self._apply_circuit_gates(state)
        yield from self._display_results(state)

        self._result_state = state
        self.measure_button.setEnabled(True)

    def _apply_circuit_gates(self, state: QuantumState) -> Iterator[None]:
        # Gates may be placed in any order. Time steps determine the execution order.
        for gate in sorted(self._gates, key=lambda gate: gate.step):
            state.apply_gate(gate.name, *gate.wires)
            yield

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
        if self._result_state is None:
            return

        basis = self._result_state.measure()
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
    font = app.font()
    font.setPointSize(10)
    if sys.platform == "win32":
        font.setFamily("Segoe UI")
    app.setFont(font)
    window = SimulatorWindow()
    window.show()
    return app.exec()

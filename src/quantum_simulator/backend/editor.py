"""Apply circuit editing rules for any frontend."""

from collections.abc import Iterator
from enum import Enum, auto

from .circuit import Circuit, PlacedGate, validate_cell
from .gate_library import GateLibrary
from .runner import RunSettings, apply_gates, prepare_state
from .state import QuantumState

_DEFAULT_GATE = "H"


class Placement(Enum):
    """What happened when the user chose a wire for the selected gate."""

    WAITING = auto()
    PLACED = auto()
    REPEATED_WIRE = auto()
    BLOCKED = auto()


class EditorSession:
    """Hold the circuit being edited, the gate being placed, and the last run's result."""

    def __init__(self, qubits: int):
        self.qubits = qubits
        self.gates: list[PlacedGate] = []
        self.selected_gate = _DEFAULT_GATE
        self.pending_step: int | None = None
        self.pending_wires: tuple[int, ...] = ()
        self.library = GateLibrary()
        self.settings: RunSettings | None = None
        self.result: QuantumState | None = None
        self.modified = False
        self._column_count = 0
        self._run_number = 0

    @property
    def column_count(self) -> int:
        """The number of columns, including empty columns at the end of an opened circuit."""
        occupied_columns = max((gate.step + 1 for gate in self.gates), default=0)
        return max(self._column_count, occupied_columns)

    @property
    def pending_role(self) -> str | None:
        """The wire role the selected gate needs next, or None when no gate is waiting."""
        if self.pending_step is None:
            return None
        return self.library.spec(self.selected_gate).wire_roles[len(self.pending_wires)]

    def fits(self, gate_id: str) -> bool:
        """Whether the register has enough wires for the gate."""
        return self.library.spec(gate_id).wire_count <= self.qubits

    def set_qubit_count(self, qubits: int) -> None:
        """Resize the register and remove gates on wires that no longer exist."""
        if qubits != self.qubits:
            self.modified = True
        self.qubits = qubits
        self.gates = [gate for gate in self.gates if max(gate.wires) < qubits]
        if not self.fits(self.selected_gate):
            self.selected_gate = _DEFAULT_GATE
        self.reset_placement()
        self.invalidate_result()

    def select_gate(self, gate_id: str) -> None:
        self.selected_gate = gate_id
        self.reset_placement()

    def reset_placement(self) -> None:
        self.pending_step = None
        self.pending_wires = ()

    def place(self, step: int, wire: int) -> Placement:
        """Add a wire to the selected gate, and place the gate once it has all its wires."""
        validate_cell(step, wire, self.qubits)
        # Choosing another column starts a new gate at its first wire.
        if self.pending_step is not None and self.pending_step != step:
            self.reset_placement()

        if wire in self.pending_wires:
            return Placement.REPEATED_WIRE

        chosen_wires = self.pending_wires + (wire,)
        gate = PlacedGate(step, self.selected_gate, chosen_wires)
        if any(gate.overlaps(placed_gate) for placed_gate in self.gates):
            return Placement.BLOCKED

        if len(chosen_wires) < self.library.spec(gate.name).wire_count:
            self.pending_step = step
            self.pending_wires = chosen_wires
            return Placement.WAITING

        self.gates.append(gate)
        self.modified = True
        self.reset_placement()
        self.invalidate_result()
        return Placement.PLACED

    def remove_at(self, step: int, wire: int) -> bool:
        """Remove the gate that crosses this cell. Return whether a gate was removed."""
        self.reset_placement()
        for gate in self.gates:
            if gate.step == step and wire in gate.wire_span:
                self.gates.remove(gate)
                self.modified = True
                self.invalidate_result()
                return True
        return False

    def clear(self) -> None:
        if self.gates:
            self.modified = True
        self.gates.clear()
        self._column_count = 0
        self.reset_placement()
        self.invalidate_result()

    def load(self, circuit: Circuit, settings: RunSettings | None = None) -> None:
        """Replace the edited circuit with an opened one. Later runs use its settings.

        The circuit's gate definitions join the library. If one clashes with a different gate
        of the same name, ValueError is raised and nothing changes.
        """
        self.library.add(*circuit.definitions)
        self.qubits = circuit.qubits
        self.gates = list(circuit.gates)
        self._column_count = circuit.column_count
        self.settings = settings
        self.modified = False
        if not self.fits(self.selected_gate):
            self.selected_gate = _DEFAULT_GATE
        self.reset_placement()
        self.invalidate_result()

    def gates_removed_by(self, qubits: int) -> list[PlacedGate]:
        """Return the placed gates that a register of this size would remove."""
        return [gate for gate in self.gates if max(gate.wires) >= qubits]

    def deletion_blocker(self, gate_id: str) -> str | None:
        """Explain why a gate cannot be deleted, or return None if it can."""
        if self.library.is_builtin(gate_id):
            return "Built-in gates cannot be deleted."
        placements = sum(gate.name == gate_id for gate in self.gates)
        if placements:
            return f"Remove {gate_id} from the circuit first. It is placed {placements} time(s)."
        dependents = self.library.dependents(gate_id)
        if dependents:
            return f"{', '.join(dependents)} is built from {gate_id}. Delete {', '.join(dependents)} first."
        return None

    def delete_gate(self, gate_id: str) -> None:
        """Delete an unused user gate. Raise ValueError with the reason if it is in use."""
        blocker = self.deletion_blocker(gate_id)
        if blocker is not None:
            raise ValueError(blocker)
        self.library.remove(gate_id)
        if self.selected_gate == gate_id:
            self.selected_gate = _DEFAULT_GATE
            self.reset_placement()

    def invalidate_result(self) -> None:
        """Discard the result and prevent an earlier run from publishing another."""
        self._run_number += 1
        self.result = None

    def circuit(self, initial_bits: str) -> Circuit:
        """Return the placed gates and the user gates they need. A gate still waiting for wires is left out."""
        definitions = self.library.definitions_for(gate.name for gate in self.gates)
        return Circuit(self.qubits, initial_bits, tuple(self.gates), self.column_count, definitions)

    def run_steps(self, initial_bits: str) -> Iterator[None]:
        """Run the circuit one gate per step, then keep its final state as the result."""
        self.invalidate_result()
        return self._run_circuit(self.circuit(initial_bits), self._run_number)

    def _run_circuit(self, circuit: Circuit, run_number: int) -> Iterator[None]:
        if run_number != self._run_number:
            return
        state = prepare_state(circuit, self.settings)
        for _ in apply_gates(state, circuit):
            yield
            if run_number != self._run_number:
                return
        self.result = state

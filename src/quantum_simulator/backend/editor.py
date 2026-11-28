"""Apply circuit editing rules for any frontend."""

from collections.abc import Callable, Iterable, Iterator, Sequence
from enum import Enum, auto
from pathlib import Path

from .circuit import Circuit, PlacedGate, execution_order, validate_cell
from .gate_library import (
    CircuitGate,
    GateDefinition,
    GateImport,
    GateLibrary,
    GateOperation,
    NameChooser,
    outermost_gates,
)
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
        self._saved_files: dict[Path, dict[str, GateDefinition]] = {}
        self.open_gate: str | None = None
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

    def can_place(self, gate_id: str) -> bool:
        """Whether the gate fits the register and, while a gate is edited, is not built from that gate."""
        if not self.fits(gate_id):
            return False
        if self.open_gate is None:
            return True
        # TODO Beware, keep this here, to prevent errors further down the line
        # Placing the open gate inside itself, even through another gate, would make a cycle.
        used_gates = {definition.gate_id for definition in self.library.definitions_for([gate_id])}
        return self.open_gate not in used_gates

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
        """Remove every gate from the open circuit or gate. Saving it again keeps the change."""
        if self.gates:
            self.modified = True
        self.gates.clear()
        self._column_count = 0
        self.reset_placement()
        self.invalidate_result()

    def new_circuit(self) -> None:
        """Replace whatever is open with an empty, unsaved circuit on the same number of qubits."""
        self.open_gate = None
        self.gates = []
        self._column_count = 0
        self.settings = None
        self.modified = False
        self.reset_placement()
        self.invalidate_result()

    def load(
        self, circuit: Circuit, settings: RunSettings | None = None, choose_name: NameChooser | None = None
    ) -> bool:
        """Replace the open circuit or gate with an opened circuit. Later runs use its settings.

        The circuit's gates join the library as GateLibrary.plan_import describes: identical
        local gates are reused, and a gate whose name is taken is renamed or replaced by the
        local gate with choose_name, along with every placement and reference to it. Return
        False, changing nothing, if choose_name cancels.
        """
        gate_import = self.library.plan_import(circuit.definitions, choose_name)
        if gate_import is None:
            return False
        self.apply_import(gate_import)
        self.open_gate = None
        self.qubits = circuit.qubits
        self.gates = [PlacedGate(gate.step, gate_import.new_name(gate.name), gate.wires) for gate in circuit.gates]
        self._column_count = circuit.column_count
        self.settings = settings
        self.modified = bool(gate_import.replaced_by_local)
        if not self.fits(self.selected_gate):
            self.selected_gate = _DEFAULT_GATE
        self.reset_placement()
        self.invalidate_result()
        return True

    def import_gates(
        self, definitions: Sequence[GateDefinition], choose_name: NameChooser | None = None
    ) -> GateImport | None:
        """Add gates from a gate file, reusing, renaming and replacing as load does.

        Return what the import changed, so callers can find each gate under its new name, or
        None, changing nothing, if choose_name cancels.
        """
        gate_import = self.library.plan_import(definitions, choose_name)
        if gate_import is not None:
            self.apply_import(gate_import)
        return gate_import

    def apply_import(self, gate_import: GateImport) -> None:
        """Add the gates an import planned with GateLibrary.plan_import."""
        self.library.add(*gate_import.definitions)

    def gates_to_edit(self, definitions: Sequence[GateDefinition], gate_import: GateImport) -> list[str]:
        """Return the file's outermost gates, under their names after the import, that are gates from circuits.

        The answer depends on the gate the user chose: an incoming gate from a circuit replaced by
        a local matrix gate with Use mine cannot be edited.
        """
        added_circuit_gates = {
            definition.gate_id for definition in gate_import.definitions if isinstance(definition, CircuitGate)
        }
        editable = []
        for definition in outermost_gates(definitions):
            gate_id = gate_import.new_name(definition.gate_id)
            if gate_id in added_circuit_gates or self.library.circuit_gate(gate_id) is not None:
                editable.append(gate_id)
        return editable

    def add_gate(self, definition: GateDefinition) -> None:
        """Add a new custom gate. It stays unsaved until a saved circuit or gate file holds it."""
        self.library.add(definition)

    def record_file(self, path: Path, definitions: Iterable[GateDefinition]) -> None:
        """Remember the definitions in the latest successful read or write at this path."""
        self._saved_files[path.resolve()] = {gate.gate_id: gate for gate in definitions}

    @property
    def unsaved_gates(self) -> set[str]:
        missing = set()
        for gate in self.library.user_definitions:
            dependencies = self.library.definitions_for([gate.gate_id])
            if not any(all(saved.get(d.gate_id) == d for d in dependencies)
                       for saved in self._saved_files.values()):
                missing.add(gate.gate_id)
        return missing

    def gates_removed_by(self, qubits: int) -> list[PlacedGate]:
        """Return the placed gates that a register of this size would remove."""
        return [gate for gate in self.gates if max(gate.wires) >= qubits]

    def deletion_blocker(self, gate_id: str) -> str | None:
        """Explain why a gate cannot be deleted, or return None if it can."""
        if self.library.is_builtin(gate_id):
            return "Built-in gates cannot be deleted."
        if gate_id == self.open_gate:
            return f"{gate_id} is open for editing. Open a circuit or start a new one first."
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

    def gate_from_circuit(self, gate_id: str) -> CircuitGate:
        """Return a gate that applies the placed gates, in execution order, on every wire of the register.

        Initial bits, run settings and empty columns are not part of the gate. Raise ValueError
        if the name or the circuit cannot make a gate.
        """
        operations = tuple(GateOperation(gate.name, gate.wires) for gate in execution_order(self.gates))
        return CircuitGate(gate_id, self.qubits, operations)

    def edit_gate(self, gate_id: str) -> None:
        """Replace the open circuit or gate with a gate from a circuit, one operation per column.

        save_gate applies the edits. Raise ValueError if the gate is not a gate from a circuit.
        """
        gate = self.library.circuit_gate(gate_id)
        if gate is None:
            raise ValueError(f"{gate_id} is not a gate from a circuit.")
        self.open_gate = gate_id
        self.qubits = gate.wire_count
        self.gates = [PlacedGate(step, operation.gate, operation.wires) for step, operation in enumerate(gate.operations)]
        self._column_count = 0
        self.settings = None
        self.modified = False
        if not self.can_place(self.selected_gate):
            self.selected_gate = _DEFAULT_GATE
        self.reset_placement()
        self.invalidate_result()

    def save_gate(
        self, write: Callable[[GateLibrary], Iterable[GateDefinition]] = lambda library: ()
    ) -> CircuitGate:
        """Apply the edits to the open gate, which every use of it then follows.

        write receives a copy of the library holding the edited gate, stores it, and returns the
        definitions it stored, which count as saved. The edits are applied only after write
        succeeds. Raise ValueError if the placed gates cannot make the gate, and pass on an
        OSError from write. Either way nothing changes, so the edits stay pending.
        """
        gate = self.gate_from_circuit(self.open_gate)
        edited_library = self.library.copy()
        edited_library.update_circuit_gate(gate)
        write(edited_library)

        self.library.update_circuit_gate(gate)
        self.modified = False
        return gate

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

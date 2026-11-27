"""Apply circuit editing rules for any frontend, without Qt."""

from collections.abc import Iterator
from enum import Enum, auto

from .circuit import Circuit, PlacedGate, validate_cell
from .gate_catalog import GATE_CATALOG
from .runner import apply_gates, prepare_state
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
        self.result: QuantumState | None = None
        self._run_number = 0

    @property
    def pending_role(self) -> str | None:
        """The wire role the selected gate needs next, or None when no gate is waiting."""
        if self.pending_step is None:
            return None
        return GATE_CATALOG[self.selected_gate].wire_roles[len(self.pending_wires)]

    def fits(self, gate_id: str) -> bool:
        """Whether the register has enough wires for the gate."""
        return GATE_CATALOG[gate_id].wire_count <= self.qubits

    def set_qubit_count(self, qubits: int) -> None:
        """Resize the register and remove gates on wires that no longer exist."""
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

        if len(chosen_wires) < GATE_CATALOG[gate.name].wire_count:
            self.pending_step = step
            self.pending_wires = chosen_wires
            return Placement.WAITING

        self.gates.append(gate)
        self.reset_placement()
        self.invalidate_result()
        return Placement.PLACED

    def remove_at(self, step: int, wire: int) -> bool:
        """Remove the gate that crosses this cell. Return whether a gate was removed."""
        self.reset_placement()
        for gate in self.gates:
            if gate.step == step and wire in gate.wire_span:
                self.gates.remove(gate)
                self.invalidate_result()
                return True
        return False

    def clear(self) -> None:
        self.gates.clear()
        self.reset_placement()
        self.invalidate_result()

    def invalidate_result(self) -> None:
        """Discard the result and prevent an earlier run from publishing another."""
        self._run_number += 1
        self.result = None

    def circuit(self, initial_bits: str) -> Circuit:
        """Return the placed gates as a circuit. A gate still waiting for wires is left out."""
        return Circuit(self.qubits, initial_bits, tuple(self.gates))

    def run_steps(self, initial_bits: str) -> Iterator[None]:
        """Run the circuit one gate per step, then keep its final state as the result."""
        self.invalidate_result()
        return self._run_circuit(self.circuit(initial_bits), self._run_number)

    def _run_circuit(self, circuit: Circuit, run_number: int) -> Iterator[None]:
        if run_number != self._run_number:
            return
        state = prepare_state(circuit)
        for _ in apply_gates(state, circuit):
            yield
            if run_number != self._run_number:
                return
        self.result = state

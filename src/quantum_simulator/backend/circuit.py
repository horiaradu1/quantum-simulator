"""Describe a circuit as placed gates and convert it to and from the versioned circuit format."""

from collections.abc import Iterable
from dataclasses import dataclass

from .gate_library import MAX_QUBITS, GateDefinition, GateLibrary, definition_from_dict

FORMAT_VERSION = 1


def validate_cell(step: int, wire: int, qubits: int) -> None:
    """Check a column and wire before accepting a placement."""
    if type(step) is not int or step < 0:
        raise ValueError("A column index must be a nonnegative integer.")
    if type(wire) is not int or not 0 <= wire < qubits:
        raise ValueError(f"columns[{step}]: wire indices must be integers from 0 to {qubits - 1}.")


@dataclass(frozen=True)
class PlacedGate:
    """A gate's circuit column, catalog ID, and wires in the order supplied to the backend."""

    step: int
    name: str
    wires: tuple[int, ...]

    @property
    def wire_span(self) -> range:
        """Rows crossed by the gate's symbol."""
        return range(min(self.wires), max(self.wires) + 1)

    def overlaps(self, other: "PlacedGate") -> bool:
        other_wires = other.wire_span
        return self.step == other.step and any(wire in other_wires for wire in self.wire_span)


def execution_order(gates: Iterable[PlacedGate]) -> list[PlacedGate]:
    """Order gates by column. Gates in the same column keep their placement order."""
    return sorted(gates, key=lambda gate: gate.step)


@dataclass(frozen=True)
class Circuit:
    """A register size, its starting basis state, the gates placed on it, and any user gates they use.

    Every rule is checked when a circuit is built, so anything that can be saved can be opened again.
    """

    qubits: int
    initial_bits: str
    gates: tuple[PlacedGate, ...] = ()
    column_count: int | None = None
    definitions: tuple[GateDefinition, ...] = ()

    def __post_init__(self):
        self._check_register()
        library = self.gate_library()
        for gate in self.gates:
            self._check_gate(gate, library)
        self._check_overlaps()

        occupied_columns = max((gate.step + 1 for gate in self.gates), default=0)
        if self.column_count is None:
            object.__setattr__(self, "column_count", occupied_columns)
        elif type(self.column_count) is not int or self.column_count < occupied_columns:
            raise ValueError("The column count must be a nonnegative integer covering every gate.")

    def gate_library(self) -> GateLibrary:
        """Return the built-in gates plus this circuit's definitions."""
        return GateLibrary(self.definitions)

    def execution_order(self) -> list[PlacedGate]:
        """Order gates by column. Gates in the same column keep their placement order."""
        return execution_order(self.gates)

    def to_dict(self) -> dict:
        """Write the circuit document. Empty columns stay as empty lists."""
        columns = [[] for _ in range(self.column_count)]
        for gate in self.gates:
            columns[gate.step].append({"gate": gate.name, "wires": list(gate.wires)})
        document = {
            "kind": "circuit",
            "version": FORMAT_VERSION,
            "qubits": self.qubits,
            "initial_bits": self.initial_bits,
            "columns": columns,
        }
        if self.definitions:
            document["definitions"] = [definition.to_dict() for definition in self.definitions]
        return document

    @classmethod
    def from_dict(cls, document: object) -> "Circuit":
        """Read a circuit document. Raise ValueError with a readable message if it is invalid."""
        if not isinstance(document, dict) or document.get("kind") != "circuit":
            raise ValueError('Expected a circuit document with "kind": "circuit".')
        if type(document.get("version")) is not int or document["version"] != FORMAT_VERSION:
            raise ValueError(f"Unsupported circuit format version {document.get('version')!r}.")

        definitions = document.get("definitions", [])
        if not isinstance(definitions, list):
            raise ValueError('"definitions" must be a list of gate definitions.')

        columns = document.get("columns")
        if not isinstance(columns, list):
            raise ValueError('"columns" must be a list of columns.')
        gates = []
        for step, column in enumerate(columns):
            if not isinstance(column, list):
                raise ValueError(f"columns[{step}] must be a list of gates.")
            for placement in column:
                gates.append(_read_placement(placement, step))

        return cls(
            document.get("qubits"),
            document.get("initial_bits"),
            tuple(gates),
            column_count=len(columns),
            definitions=tuple(definition_from_dict(definition) for definition in definitions),
        )

    def _check_register(self) -> None:
        if type(self.qubits) is not int or not 1 <= self.qubits <= MAX_QUBITS:
            raise ValueError(f'"qubits" must be an integer from 1 to {MAX_QUBITS}.')
        is_bit_string = isinstance(self.initial_bits, str) and set(self.initial_bits) <= {"0", "1"}
        if not is_bit_string or len(self.initial_bits) != self.qubits:
            raise ValueError(f'"initial_bits" must be {self.qubits} characters, each 0 or 1.')

    def _check_gate(self, gate: PlacedGate, library: GateLibrary) -> None:
        location = f"columns[{gate.step}]"
        if gate.name not in library:
            raise ValueError(f"{location}: unknown gate {gate.name!r}.")
        wire_count = library.spec(gate.name).wire_count
        if len(gate.wires) != wire_count:
            raise ValueError(f"{location}: {gate.name} acts on {wire_count} wire(s), not {len(gate.wires)}.")
        for wire in gate.wires:
            validate_cell(gate.step, wire, self.qubits)
        if len(set(gate.wires)) != len(gate.wires):
            raise ValueError(f"{location}: gate wires must be distinct.")

    def _check_overlaps(self) -> None:
        for index, gate in enumerate(self.gates):
            for earlier_gate in self.gates[:index]:
                if gate.overlaps(earlier_gate):
                    raise ValueError(
                        f"columns[{gate.step}]: {earlier_gate.name} and {gate.name} cross the same wires."
                    )


def _read_placement(placement: object, step: int) -> PlacedGate:
    location = f"columns[{step}]"
    if not isinstance(placement, dict):
        raise ValueError(f'{location}: each gate must be an object with "gate" and "wires".')
    gate_id = placement.get("gate")
    if not isinstance(gate_id, str):
        raise ValueError(f"{location}: unknown gate {gate_id!r}.")
    wires = placement.get("wires")
    if not isinstance(wires, list):
        raise ValueError(f'{location}: "wires" of {gate_id} must be a list of wire indices.')
    return PlacedGate(step, gate_id, tuple(wires))

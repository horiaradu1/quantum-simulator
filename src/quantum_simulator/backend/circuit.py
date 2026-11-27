"""Describe a circuit as placed gates and read it from the versioned circuit format."""

from dataclasses import dataclass

from .gate_catalog import GATE_CATALOG

FORMAT_VERSION = 1
MAX_QUBITS = 20


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


@dataclass(frozen=True)
class Circuit:
    """A register size, its starting basis state, and the gates placed on it."""

    qubits: int
    initial_bits: str
    gates: tuple[PlacedGate, ...] = ()
    column_count: int | None = None

    def __post_init__(self):
        occupied_columns = 0
        for gate in self.gates:
            if not gate.wires:
                raise ValueError(f"columns[{gate.step}]: a gate needs at least one wire.")
            for wire in gate.wires:
                validate_cell(gate.step, wire, self.qubits)
            if len(set(gate.wires)) != len(gate.wires):
                raise ValueError(f"columns[{gate.step}]: gate wires must be distinct.")
            occupied_columns = max(occupied_columns, gate.step + 1)

        if self.column_count is None:
            object.__setattr__(self, "column_count", occupied_columns)
        elif type(self.column_count) is not int or self.column_count < occupied_columns:
            raise ValueError("The column count must be a nonnegative integer covering every gate.")

    def execution_order(self) -> list[PlacedGate]:
        """Order gates by column. Gates in the same column keep their placement order."""
        return sorted(self.gates, key=lambda gate: gate.step)

    @classmethod
    def from_dict(cls, document: object) -> "Circuit":
        """Read a circuit document. Raise ValueError with a readable message if it is invalid."""
        if not isinstance(document, dict) or document.get("kind") != "circuit":
            raise ValueError('Expected a circuit document with "kind": "circuit".')
        if type(document.get("version")) is not int or document["version"] != FORMAT_VERSION:
            raise ValueError(f"Unsupported circuit format version {document.get('version')!r}.")

        qubits = document.get("qubits")
        if type(qubits) is not int or not 1 <= qubits <= MAX_QUBITS:
            raise ValueError(f'"qubits" must be an integer from 1 to {MAX_QUBITS}.')

        initial_bits = document.get("initial_bits")
        is_bit_string = isinstance(initial_bits, str) and set(initial_bits) <= {"0", "1"}
        if not is_bit_string or len(initial_bits) != qubits:
            raise ValueError(f'"initial_bits" must be {qubits} characters, each 0 or 1.')

        columns = document.get("columns")
        if not isinstance(columns, list):
            raise ValueError('"columns" must be a list of columns.')
        gates = []
        for step, column in enumerate(columns):
            if not isinstance(column, list):
                raise ValueError(f"columns[{step}] must be a list of gates.")
            for placement in column:
                gates.append(_read_placement(placement, step))
        return cls(qubits, initial_bits, tuple(gates), column_count=len(columns))


def _read_placement(placement: object, step: int) -> PlacedGate:
    location = f"columns[{step}]"
    if not isinstance(placement, dict):
        raise ValueError(f'{location}: each gate must be an object with "gate" and "wires".')

    gate_id = placement.get("gate")
    if not isinstance(gate_id, str) or gate_id not in GATE_CATALOG:
        raise ValueError(f"{location}: unknown gate {gate_id!r}.")

    wires = placement.get("wires")
    if not isinstance(wires, list):
        raise ValueError(f'{location}: "wires" of {gate_id} must be a list of wire indices.')
    wire_count = GATE_CATALOG[gate_id].wire_count
    if len(wires) != wire_count:
        raise ValueError(f"{location}: {gate_id} acts on {wire_count} wire(s), not {len(wires)}.")
    return PlacedGate(step, gate_id, tuple(wires))

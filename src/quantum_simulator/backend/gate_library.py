"""Define user gates and look up any gate's matrix, label and wire roles in one place.

A matrix gate is given by its unitary matrix. A controlled gate adds one control wire before
the wires of an existing gate. A gate from a circuit applies a sequence of other gates to its own
wires. All three are written to JSON as definitions with an "id", "kind" and "wire_count".
"""

import re
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .gate_catalog import GATE_CATALOG, GateSpec, WireMark
from .gates import BUILTIN_GATE_IDS, gate_matrix, unitary_matrix
from .state import QuantumState

# A circuit must have at most this many qubits.
# The limit is checked for every circuit and gate, so a manually edited file fails.
MAX_QUBITS = 20
MAX_MATRIX_WIRES = 3
MAX_NAME_LENGTH = 8
_GATE_NAME = re.compile(rf"[A-Za-z][A-Za-z0-9_]{{0,{MAX_NAME_LENGTH - 1}}}")
_ORDINALS = (
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
    "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth",
    "eighteenth", "nineteenth", "twentieth",
)


def validate_gate_name(gate_id: object) -> None:
    if not isinstance(gate_id, str) or not _GATE_NAME.fullmatch(gate_id):
        raise ValueError(
            f"Invalid gate name {gate_id!r}. Use 1 to {MAX_NAME_LENGTH} letters, digits or underscores, "
            "starting with a letter."
        )


class MatrixGate:
    """A user gate given by a unitary matrix on 1 to 3 wires."""

    kind = "matrix"

    def __init__(self, gate_id: str, matrix: ArrayLike):
        validate_gate_name(gate_id)
        try:
            entries = np.array(matrix, dtype=np.complex128)
        except (TypeError, ValueError):
            raise ValueError(f"{gate_id}: matrix entries must be numbers.") from None

        sizes = {2**wire_count: wire_count for wire_count in range(1, MAX_MATRIX_WIRES + 1)}
        if entries.ndim != 2 or entries.shape[0] not in sizes:
            raise ValueError(f"{gate_id}: the matrix must be 2×2, 4×4 or 8×8.")
        try:
            self.matrix = unitary_matrix(entries, sizes[entries.shape[0]])
        except ValueError as error:
            raise ValueError(f"{gate_id}: {error}") from None
        self.gate_id = gate_id

    @property
    def wire_count(self) -> int:
        return self.matrix.shape[0].bit_length() - 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MatrixGate):
            return NotImplemented
        return self.gate_id == other.gate_id and np.array_equal(self.matrix, other.matrix)

    def __repr__(self) -> str:
        return f"MatrixGate({self.gate_id!r}, wire_count={self.wire_count})"

    def to_dict(self) -> dict:
        rows = []
        for row in self.matrix:
            rows.append([[float(entry.real), float(entry.imag)] for entry in row])
        return {"id": self.gate_id, "kind": self.kind, "wire_count": self.wire_count, "matrix": rows}


@dataclass(frozen=True)
class ControlledGate:
    """A user gate that adds one control wire before the wires of its base gate."""

    gate_id: str
    base: str
    wire_count: int

    kind: ClassVar[str] = "controlled"

    def __post_init__(self):
        validate_gate_name(self.gate_id)
        if not isinstance(self.base, str):
            raise ValueError(f"{self.gate_id}: the base gate must be a gate name.")
        if type(self.wire_count) is not int or self.wire_count < 2:
            raise ValueError(f"{self.gate_id}: a controlled gate acts on at least 2 wires.")

    def to_dict(self) -> dict:
        return {"id": self.gate_id, "kind": self.kind, "wire_count": self.wire_count, "base": self.base}


@dataclass(frozen=True)
class GateOperation:
    """One step of a gate from a circuit: a gate and the local wires it acts on, in gate order."""

    gate: str
    wires: tuple[int, ...]

    def __post_init__(self):
        if not isinstance(self.gate, str):
            raise ValueError("Each operation must name a gate.")
        if not isinstance(self.wires, (list, tuple)):
            raise ValueError(f"The wires of {self.gate} must be a list of wire indices.")
        object.__setattr__(self, "wires", tuple(self.wires))


@dataclass(frozen=True)
class CircuitGate:
    """A user gate that applies other gates in order to its local wires, numbered from 0."""

    gate_id: str
    wire_count: int
    operations: tuple[GateOperation, ...]

    kind: ClassVar[str] = "circuit_gate"

    def __post_init__(self):
        validate_gate_name(self.gate_id)
        if type(self.wire_count) is not int or not 1 <= self.wire_count <= MAX_QUBITS:
            raise ValueError(f"{self.gate_id}: a gate from a circuit acts on 1 to {MAX_QUBITS} wires.")
        object.__setattr__(self, "operations", tuple(self.operations))
        if not self.operations:
            raise ValueError(f"{self.gate_id}: a gate from a circuit needs at least one gate placed in it.")
        for number, operation in enumerate(self.operations, start=1):
            wires = operation.wires
            in_range = all(type(wire) is int and 0 <= wire < self.wire_count for wire in wires)
            if not wires or not in_range:
                raise ValueError(
                    f"{self.gate_id}: operation {number} ({operation.gate}) needs wires from 0 to {self.wire_count - 1}."
                )
            if len(set(wires)) != len(wires):
                raise ValueError(f"{self.gate_id}: operation {number} ({operation.gate}) repeats a wire.")

    def to_dict(self) -> dict:
        operations = [{"gate": operation.gate, "wires": list(operation.wires)} for operation in self.operations]
        return {"id": self.gate_id, "kind": self.kind, "wire_count": self.wire_count, "operations": operations}


type GateDefinition = MatrixGate | ControlledGate | CircuitGate


class ClashChoice(Enum):
    """An answer to a name clash other than a new name."""

    USE_LOCAL = auto()


@dataclass(frozen=True)
class NameClash:
    """An incoming gate whose name is taken, a free name to suggest, and whether the local gate can stand in."""

    incoming: GateDefinition
    problem: str
    suggestion: str
    can_use_local: bool


type NameChooser = Callable[[NameClash], str | ClashChoice | None]


@dataclass(frozen=True, eq=False)
class MatrixOperation:
    """A matrix applied to target wires, only where every control wire is 1."""

    matrix: NDArray[np.complex128]
    targets: tuple[int, ...]
    controls: tuple[int, ...] = ()


@dataclass(frozen=True)
class GateImport:
    """What an import changes: the gates it adds, the incoming gates it renamed, and those replaced by local gates."""

    definitions: tuple[GateDefinition, ...]
    renames: dict[str, str] = field(default_factory=dict)
    replaced_by_local: dict[str, str] = field(default_factory=dict)

    def new_name(self, gate_id: str) -> str:
        """The name an incoming placement or reference to this gate uses after the import."""
        return self.renames.get(gate_id) or self.replaced_by_local.get(gate_id, gate_id)


def definition_from_dict(document: object) -> GateDefinition:
    """Read one gate definition. Raise ValueError with a readable message if it is invalid."""
    if not isinstance(document, dict):
        raise ValueError("Each gate definition must be an object.")
    gate_id = document.get("id")
    kind = document.get("kind")
    if kind == "matrix":
        definition = MatrixGate(gate_id, _read_matrix(gate_id, document.get("matrix")))
    elif kind == "controlled":
        definition = ControlledGate(gate_id, document.get("base"), document.get("wire_count"))
    elif kind == "circuit_gate":
        operations = _read_operations(gate_id, document.get("operations"))
        definition = CircuitGate(gate_id, document.get("wire_count"), operations)
    else:
        raise ValueError(f"{gate_id}: unknown definition kind {kind!r}.")

    if document.get("wire_count") != definition.wire_count:
        raise ValueError(f"{gate_id}: wire_count must be {definition.wire_count}.")
    return definition


def renamed(definition: GateDefinition, names: Mapping[str, str]) -> GateDefinition:
    """Return the definition with its ID and every gate it references changed according to names."""

    def new_name(gate_id: str) -> str:
        return names.get(gate_id, gate_id)

    if isinstance(definition, MatrixGate):
        return MatrixGate(new_name(definition.gate_id), definition.matrix)
    if isinstance(definition, ControlledGate):
        return ControlledGate(new_name(definition.gate_id), new_name(definition.base), definition.wire_count)
    operations = tuple(GateOperation(new_name(operation.gate), operation.wires) for operation in definition.operations)
    return CircuitGate(new_name(definition.gate_id), definition.wire_count, operations)


def outermost_gates(definitions: Sequence[GateDefinition]) -> list[GateDefinition]:
    """Return the definitions that no other definition in the list is built from.

    In a gate file, that is the gate the file was saved for, after the gates it uses.
    """
    used_gates = {reference for definition in definitions for reference in _references(definition)}
    return [definition for definition in definitions if definition.gate_id not in used_gates]


def _references(definition: GateDefinition) -> tuple[str, ...]:
    """The gates a definition is built from."""
    if isinstance(definition, ControlledGate):
        return (definition.base,)
    if isinstance(definition, CircuitGate):
        return tuple(operation.gate for operation in definition.operations)
    return ()


def _in_dependency_order(definitions: Iterable[GateDefinition]) -> list[GateDefinition]:
    """Order definitions so each comes after the definitions it references. Raise ValueError on a cycle."""
    by_id: dict[str, GateDefinition] = {}
    for definition in definitions:
        earlier = by_id.setdefault(definition.gate_id, definition)
        if earlier != definition:
            raise ValueError(f"Two different gates are named {definition.gate_id}.")

    ordered: list[GateDefinition] = []
    ordered_ids: set[str] = set()
    visiting: list[str] = []

    def visit(gate_id: str) -> None:
        definition = by_id.get(gate_id)
        if definition is None or gate_id in ordered_ids:
            return
        if gate_id in visiting:
            cycle = [*visiting[visiting.index(gate_id):], gate_id]
            raise ValueError(f"Gate definitions form a cycle: {' → '.join(cycle)}.")
        visiting.append(gate_id)
        for reference in _references(definition):
            visit(reference)
        visiting.pop()
        ordered.append(definition)
        ordered_ids.add(gate_id)

    for gate_id in by_id:
        visit(gate_id)
    return ordered


def _wire_roles(wire_count: int) -> tuple[str, ...]:
    """Roles for a gate whose wires have no special meaning: "target", or "first wire", "second wire" and so on."""
    if wire_count == 1:
        return ("target",)
    return tuple(f"{ordinal} wire" for ordinal in _ORDINALS[:wire_count])


def _read_matrix(gate_id: object, rows: object) -> list[list[complex]]:
    if not isinstance(rows, list) or not all(isinstance(row, list) for row in rows):
        raise ValueError(f"{gate_id}: the matrix must be a list of rows.")
    matrix = []
    for row in rows:
        matrix.append([_complex_from_pair(gate_id, entry) for entry in row])
    return matrix


def _complex_from_pair(gate_id: object, entry: object) -> complex:
    is_pair = isinstance(entry, list) and len(entry) == 2
    if not is_pair or not all(type(part) in (int, float) for part in entry):
        raise ValueError(f"{gate_id}: each matrix entry must be a [real, imaginary] pair of numbers.")
    real, imaginary = entry
    return complex(real, imaginary)


def _read_operations(gate_id: object, operations: object) -> tuple[GateOperation, ...]:
    if not isinstance(operations, list):
        raise ValueError(f'{gate_id}: "operations" must be a list.')
    read = []
    for number, operation in enumerate(operations, start=1):
        if not isinstance(operation, dict) or not isinstance(operation.get("wires"), list):
            raise ValueError(f'{gate_id}: operation {number} must be an object with "gate" and "wires".')
        read.append(GateOperation(operation.get("gate"), tuple(operation["wires"])))
    return tuple(read)


class GateLibrary:
    """Built-in gates plus user definitions, in palette order."""

    def __init__(self, definitions: Iterable[GateDefinition] = ()):
        self._definitions: dict[str, GateDefinition] = {}
        for definition in _in_dependency_order(definitions):
            self._register(definition)

    @property
    def user_definitions(self) -> tuple[GateDefinition, ...]:
        return tuple(self._definitions.values())

    def copy(self) -> "GateLibrary":
        """Return a separate library with the same user gates, to try a change without making it."""
        return GateLibrary(self.user_definitions)

    def gate_ids(self) -> list[str]:
        return [*GATE_CATALOG, *self._definitions]

    def circuit_gate(self, gate_id: str) -> CircuitGate | None:
        """Return the gate from a circuit with this ID, or None if there is none."""
        definition = self._definitions.get(gate_id)
        return definition if isinstance(definition, CircuitGate) else None

    def update_circuit_gate(self, gate: CircuitGate) -> None:
        """Replace a gate from a circuit with an edited version, which every use then applies.

        Raise ValueError, changing nothing, if the name or wire count differs or the edit makes a cycle.
        """
        original = self.circuit_gate(gate.gate_id)
        if original is None or original.wire_count != gate.wire_count:
            raise ValueError("An edited gate must keep its name and wire count.")
        updated = GateLibrary(gate if definition is original else definition for definition in self.user_definitions)
        self._definitions = updated._definitions

    def __contains__(self, gate_id: object) -> bool:
        return gate_id in GATE_CATALOG or gate_id in self._definitions

    def check(self, *definitions: GateDefinition) -> None:
        """Raise ValueError if the definitions cannot be added together."""
        staging = GateLibrary(self.user_definitions)
        for definition in _in_dependency_order(definitions):
            staging._register(definition)

    def add(self, *definitions: GateDefinition) -> None:
        """Add the definitions together, in any order. If any is invalid, raise ValueError and add none."""
        self.check(*definitions)
        for definition in _in_dependency_order(definitions):
            self._register(definition)

    def check_name(self, gate_id: object) -> None:
        """Raise ValueError unless the name is valid and no gate uses it, ignoring case."""
        validate_gate_name(gate_id)
        if gate_id.upper() in BUILTIN_GATE_IDS:
            raise ValueError(f"{gate_id} is already the name of a built-in gate.")
        existing = self._find_ignoring_case(gate_id)
        if existing is not None:
            raise ValueError(f"A gate named {existing.gate_id} already exists.")

    def name_problem(self, gate_id: object) -> str | None:
        """Explain why a new gate cannot use this name, or return None if it can."""
        try:
            self.check_name(gate_id)
        except ValueError as error:
            return str(error)
        return None

    def suggest_name(self, gate_id: str) -> str:
        """Return a free name made from gate_id and a number, such as Rot2."""
        number = 2
        while True:
            suffix = str(number)
            candidate = gate_id[: MAX_NAME_LENGTH - len(suffix)] + suffix
            if self.name_problem(candidate) is None:
                return candidate
            number += 1

    def spec(self, gate_id: str) -> GateSpec:
        """Return how editors label, place and draw the gate."""
        if gate_id in GATE_CATALOG:
            return GATE_CATALOG[gate_id]
        definition = self._definition(gate_id)
        if isinstance(definition, MatrixGate):
            description = "A custom gate defined by its matrix."
            return GateSpec(gate_id, _wire_roles(definition.wire_count), description=description)
        if isinstance(definition, CircuitGate):
            labels = [self._label(operation.gate) for operation in definition.operations]
            description = f"Applies {', '.join(labels)} in order."
            return GateSpec(gate_id, _wire_roles(definition.wire_count), description=description)
        return self._controlled_spec(definition)

    def is_builtin(self, gate_id: str) -> bool:
        return gate_id in GATE_CATALOG

    def dependents(self, gate_id: str) -> list[str]:
        """Return the user gates built directly from this gate."""
        return [
            definition.gate_id
            for definition in self._definitions.values()
            if gate_id in _references(definition)
        ]

    def remove(self, gate_id: str) -> None:
        """Remove a user gate. Raise ValueError if it is built in, unknown, or another gate uses it."""
        if self.is_builtin(gate_id):
            raise ValueError(f"{gate_id} is a built-in gate.")
        self._definition(gate_id)
        dependents = self.dependents(gate_id)
        if dependents:
            raise ValueError(f"{', '.join(dependents)} is built from {gate_id}.")
        del self._definitions[gate_id]

    def matrix_operations(self, gate_id: str, wires: Sequence[int]) -> Iterator[MatrixOperation]:
        """Break the gate, placed on these register wires, into matrices on at most 3 wires each.

        Controls and gates from circuits are applied one matrix at a time, so a wide gate never needs
        its full matrix.
        """
        wires = tuple(wires)
        if gate_id in GATE_CATALOG:
            yield MatrixOperation(gate_matrix(gate_id, len(wires)), wires)
            return
        definition = self._definition(gate_id)
        if isinstance(definition, MatrixGate):
            yield MatrixOperation(definition.matrix, wires)
        elif isinstance(definition, ControlledGate):
            control, *base_wires = wires
            for operation in self.matrix_operations(definition.base, base_wires):
                yield MatrixOperation(operation.matrix, operation.targets, (control, *operation.controls))
        else:
            for operation in definition.operations:
                # Local wire i of a gate from a circuit is the i-th wire it is placed on.
                register_wires = tuple(wires[local_wire] for local_wire in operation.wires)
                yield from self.matrix_operations(operation.gate, register_wires)

    def matrix(self, gate_id: str) -> NDArray[np.complex128]:
        """Return the gate's full matrix. It has 4^wires entries, so use it only for small gates."""
        if gate_id in GATE_CATALOG:
            return gate_matrix(gate_id, GATE_CATALOG[gate_id].wire_count)
        definition = self._definition(gate_id)
        if isinstance(definition, MatrixGate):
            return definition.matrix

        # Column j of the matrix is the state the gate makes from basis input j.
        wire_count = definition.wire_count
        operations = list(self.matrix_operations(gate_id, range(wire_count)))
        columns = []
        for basis_index in range(2**wire_count):
            state = QuantumState(wire_count)
            state.initialize(format(basis_index, f"0{wire_count}b"))
            for operation in operations:
                state.apply_gate(operation.matrix, *operation.targets, controls=operation.controls)
            columns.append(state.amplitudes)
        matrix = np.column_stack(columns)
        matrix.setflags(write=False)
        return matrix

    def definitions_for(self, gate_ids: Iterable[str]) -> tuple[GateDefinition, ...]:
        """Return the user definitions these gates need, each once, after the gates it uses."""
        needed: dict[str, GateDefinition] = {}
        for gate_id in gate_ids:
            self._collect(gate_id, needed)
        return tuple(needed.values())

    def plan_import(
        self, definitions: Sequence[GateDefinition], choose_name: NameChooser | None = None
    ) -> GateImport | None:
        """Work out how to add definitions from a file or circuit, without changing this library.

        An incoming gate identical to a local one, including its dependencies, reuses the local
        gate. When an incoming gate's name is taken, choose_name gives it a new name or, if the
        local gate of that name has the same wire count, uses the local gate instead. Every
        incoming reference follows either choice. Without choose_name, a taken name raises
        ValueError. Return None if choose_name cancels.
        """
        GateLibrary(definitions)
        staging = GateLibrary(self.user_definitions)
        renames: dict[str, str] = {}
        replaced_by_local: dict[str, str] = {}
        added = []
        for incoming in _in_dependency_order(definitions):
            definition = renamed(incoming, renames | replaced_by_local)
            local = staging._find_ignoring_case(definition.gate_id)
            if local == definition:
                continue

            choice = staging._settle_clash(definition, choose_name)
            if choice is None:
                return None
            if choice is ClashChoice.USE_LOCAL:
                replaced_by_local[incoming.gate_id] = local.gate_id
                continue
            if choice != definition.gate_id:
                renames[incoming.gate_id] = choice
                definition = renamed(incoming, renames | replaced_by_local)
            staging._register(definition)
            added.append(definition)
        return GateImport(tuple(added), renames, replaced_by_local)

    def _settle_clash(self, definition: GateDefinition, choose_name: NameChooser | None) -> str | ClashChoice | None:
        """Return a free name for an incoming definition, USE_LOCAL, or None if the user cancels."""
        gate_id = definition.gate_id
        problem = self.name_problem(gate_id)
        local = self._find_ignoring_case(gate_id)
        can_use_local = local is not None and local.wire_count == definition.wire_count
        while problem is not None:
            if choose_name is None:
                raise ValueError(problem)
            clash = NameClash(definition, problem, self.suggest_name(definition.gate_id), can_use_local)
            choice = choose_name(clash)
            if choice is None or (choice is ClashChoice.USE_LOCAL and can_use_local):
                return choice
            gate_id = choice
            problem = self.name_problem(gate_id)
        return gate_id

    def _collect(self, gate_id: str, needed: dict[str, GateDefinition]) -> None:
        definition = self._definitions.get(gate_id)
        if definition is None or gate_id in needed:
            return
        for reference in _references(definition):
            self._collect(reference, needed)
        needed[gate_id] = definition

    @staticmethod
    def _label(gate_id: str) -> str:
        # A custom gate is labelled with its ID.
        return GATE_CATALOG[gate_id].label if gate_id in GATE_CATALOG else gate_id

    def _definition(self, gate_id: str) -> GateDefinition:
        try:
            return self._definitions[gate_id]
        except KeyError:
            raise ValueError(f"Unknown gate {gate_id!r}.") from None

    def _controlled_spec(self, definition: ControlledGate) -> GateSpec:
        base = self.spec(definition.base)
        gate_id = definition.gate_id
        wire_roles = ("control", *base.wire_roles)
        base_wires = "the last wire" if base.wire_count == 1 else f"the last {base.wire_count} wires"
        description = f"Applies {base.label} to {base_wires} when the control is 1."

        if base.symbols is not None:
            return GateSpec(gate_id, wire_roles, (WireMark.CONTROL, *base.symbols), description)
        if base.wire_count == 1:
            return GateSpec(gate_id, wire_roles, (WireMark.CONTROL, base.label), description)
        # A multi-wire base keeps its box, and the new control adds a dot before it.
        return GateSpec(
            gate_id, wire_roles, description=description,
            control_count=base.control_count + 1, box_label=base.box_label or base.label,
        )

    def _register(self, definition: GateDefinition) -> None:
        if not isinstance(definition, (MatrixGate, ControlledGate, CircuitGate)):
            raise ValueError("Gate definitions must be matrix gates, controlled gates or gates from circuits.")
        gate_id = definition.gate_id
        # Opening a circuit again may repeat a definition the library already has.
        if self._find_ignoring_case(gate_id) == definition:
            return
        self.check_name(gate_id)

        if isinstance(definition, ControlledGate):
            if definition.base not in self:
                raise ValueError(f"{gate_id} controls an unknown gate {definition.base!r}.")
            expected_wires = self.spec(definition.base).wire_count + 1
            if definition.wire_count != expected_wires:
                raise ValueError(f"{gate_id} acts on {expected_wires} wires: one control plus {definition.base}.")
        elif isinstance(definition, CircuitGate):
            self._check_operations(definition)
        self._definitions[gate_id] = definition

    def _check_operations(self, definition: CircuitGate) -> None:
        for number, operation in enumerate(definition.operations, start=1):
            location = f"{definition.gate_id}: operation {number}"
            if operation.gate not in self:
                raise ValueError(f"{location} uses an unknown gate {operation.gate!r}.")
            expected_wires = self.spec(operation.gate).wire_count
            if len(operation.wires) != expected_wires:
                raise ValueError(
                    f"{location}: {operation.gate} acts on {expected_wires} wire(s), not {len(operation.wires)}."
                )

    def _find_ignoring_case(self, gate_id: str) -> GateDefinition | None:
        for definition in self._definitions.values():
            if definition.gate_id.upper() == gate_id.upper():
                return definition
        return None

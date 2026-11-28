"""Define user gates and look up any gate's matrix, label and wire roles in one place.

A matrix gate is given by its unitary matrix. A controlled gate adds one control wire before
the wires of an existing gate. Both are written to JSON as definitions with an "id", "kind"
and "wire_count".
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .gate_catalog import GATE_CATALOG, GateSpec, WireMark
from .gates import BUILTIN_GATE_IDS, controlled, gate_matrix, unitary_matrix

MAX_MATRIX_WIRES = 3
_GATE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,7}")
_WIRE_ROLES = ("first wire", "second wire", "third wire")


def validate_gate_name(gate_id: object) -> None:
    if not isinstance(gate_id, str) or not _GATE_NAME.fullmatch(gate_id):
        raise ValueError(
            f"Invalid gate name {gate_id!r}. Use 1 to 8 letters, digits or underscores, starting with a letter."
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


type GateDefinition = MatrixGate | ControlledGate


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
    else:
        raise ValueError(f"{gate_id}: unknown definition kind {kind!r}.")

    if document.get("wire_count") != definition.wire_count:
        raise ValueError(f"{gate_id}: wire_count must be {definition.wire_count}.")
    return definition


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


class GateLibrary:
    """Built-in gates plus user definitions, in palette order."""

    def __init__(self, definitions: Iterable[GateDefinition] = ()):
        self._definitions: dict[str, GateDefinition] = {}
        for definition in definitions:
            self._register(definition)

    @property
    def user_definitions(self) -> tuple[GateDefinition, ...]:
        return tuple(self._definitions.values())

    def gate_ids(self) -> list[str]:
        return [*GATE_CATALOG, *self._definitions]

    def __contains__(self, gate_id: object) -> bool:
        return gate_id in GATE_CATALOG or gate_id in self._definitions

    def check(self, *definitions: GateDefinition) -> None:
        """Raise ValueError if the definitions cannot be added together."""
        GateLibrary([*self._definitions.values(), *definitions])

    def add(self, *definitions: GateDefinition) -> None:
        """Add the definitions together. If any is invalid, raise ValueError and add none."""
        self.check(*definitions)
        for definition in definitions:
            self._register(definition)

    def check_name(self, gate_id: object) -> None:
        """Raise ValueError unless the name is valid and no gate uses it, ignoring case."""
        validate_gate_name(gate_id)
        if gate_id.upper() in BUILTIN_GATE_IDS:
            raise ValueError(f"{gate_id} is already the name of a built-in gate.")
        existing = self._find_ignoring_case(gate_id)
        if existing is not None:
            raise ValueError(f"A gate named {existing.gate_id} already exists.")

    def spec(self, gate_id: str) -> GateSpec:
        """Return how editors label, place and draw the gate."""
        if gate_id in GATE_CATALOG:
            return GATE_CATALOG[gate_id]
        definition = self._definition(gate_id)
        if isinstance(definition, MatrixGate):
            description = "A custom gate defined by its matrix."
            if definition.wire_count == 1:
                return GateSpec(gate_id, ("target",), description=description)
            return GateSpec(gate_id, _WIRE_ROLES[: definition.wire_count], description=description)
        return self._controlled_spec(definition)

    def is_builtin(self, gate_id: str) -> bool:
        return gate_id in GATE_CATALOG

    def dependents(self, gate_id: str) -> list[str]:
        """Return the user gates built directly from this gate."""
        return [
            definition.gate_id
            for definition in self._definitions.values()
            if isinstance(definition, ControlledGate) and definition.base == gate_id
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

    def matrix(self, gate_id: str) -> NDArray[np.complex128]:
        if gate_id in GATE_CATALOG:
            return gate_matrix(gate_id, GATE_CATALOG[gate_id].wire_count)
        definition = self._definition(gate_id)
        if isinstance(definition, MatrixGate):
            return definition.matrix
        return controlled(self.matrix(definition.base))

    def definitions_for(self, gate_ids: Iterable[str]) -> tuple[GateDefinition, ...]:
        """Return the user definitions these gates need, with each base before the gates that use it."""
        needed: dict[str, GateDefinition] = {}
        for gate_id in gate_ids:
            self._collect(gate_id, needed)
        return tuple(needed.values())

    def _collect(self, gate_id: str, needed: dict[str, GateDefinition]) -> None:
        definition = self._definitions.get(gate_id)
        if definition is None or gate_id in needed:
            return
        if isinstance(definition, ControlledGate):
            self._collect(definition.base, needed)
        needed[gate_id] = definition

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
        if not isinstance(definition, (MatrixGate, ControlledGate)):
            raise ValueError("Gate definitions must be matrix or controlled gates.")
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
        self._definitions[gate_id] = definition

    def _find_ignoring_case(self, gate_id: str) -> GateDefinition | None:
        for definition in self._definitions.values():
            if definition.gate_id.upper() == gate_id.upper():
                return definition
        return None

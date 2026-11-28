"""Gate matrices in computational basis order, with input states as columns.

gate_matrix looks up a built-in gate or validates a user-supplied matrix.
unitary_matrix checks a matrix and returns it as an exact unitary.
controlled adds a control wire to a gate matrix.
"""

from math import sqrt

import numpy as np
from numpy.typing import ArrayLike, NDArray


# Single-qubit gates in the basis |0>, |1>.
_SINGLE_QUBIT_GATES = {
    "X": np.array([
        [0, 1],
        [1, 0],
    ], dtype=complex),
    "Y": np.array([
        [ 0, -1j],
        [1j,   0],
    ], dtype=complex),
    "Z": np.array([
        [1,  0],
        [0, -1],
    ], dtype=complex),
    "H": np.array([
        [1,  1],
        [1, -1],
    ], dtype=complex) / sqrt(2),
    "S": np.array([
        [1,  0],
        [0, 1j],
    ], dtype=complex),
    "T": np.array([
        [1, 0],
        [0, np.exp(1j * np.pi / 4)],
    ], dtype=complex),
}

# Multi-qubit gates use the first listed wire as the leftmost basis bit.
_MULTI_QUBIT_GATES = {
    # Reverse CNOT uses the second wire as the control.
    # TODO: Remove CNOT10 and use CNOT on swapped wires.
    "CNOT10": np.array([
        [1, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
    ], dtype=complex),
    "SWAP": np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], dtype=complex),
}


def controlled(base: NDArray[np.complex128]) -> NDArray[np.complex128]:
    """Add one control before the base gate's wires.

    The control is the leftmost basis bit, so the base gate fills the block where it is 1.
    """
    size = base.shape[0]
    matrix = np.eye(2 * size, dtype=complex)
    matrix[size:, size:] = base
    return matrix


# Controlled gates take the control first, followed by the base gate's wires.
_CONTROLLED_GATES = {
    "CNOT": controlled(_SINGLE_QUBIT_GATES["X"]),
    "CH": controlled(_SINGLE_QUBIT_GATES["H"]),
    "CY": controlled(_SINGLE_QUBIT_GATES["Y"]),
    "CZ": controlled(_SINGLE_QUBIT_GATES["Z"]),
    "CS": controlled(_SINGLE_QUBIT_GATES["S"]),
    "CT": controlled(_SINGLE_QUBIT_GATES["T"]),
}
# Toffoli controls a CNOT, so it takes both controls before the target.
_CONTROLLED_GATES["TOFFOLI"] = controlled(_CONTROLLED_GATES["CNOT"])

_GATES = _SINGLE_QUBIT_GATES | _MULTI_QUBIT_GATES | _CONTROLLED_GATES
for _matrix in _GATES.values():
    _matrix.setflags(write=False)

BUILTIN_GATE_IDS = frozenset(_GATES)

# Decides whether a matrix is accepted at all. It allows values rounded to 4 decimals, like 0.7071 in a Hadamard
UNITARY_TOLERANCE = 1e-4
# Decides whether an accepted matrix is stored as typed or replaced by the nearest exact unitary. A matrix that's already exact up to floating-point noise is left unchanged.
_ROUNDING_ERROR = 1e-12


def unitarity_error(matrix: NDArray[np.complex128]) -> float:
    """Return the largest entry of U†U - I. A unitary preserves the state's norm, so this is 0."""
    identity = np.eye(matrix.shape[0])
    # Huge entries overflow U†U, which makes the error inf or NaN. Callers reject both.
    with np.errstate(over="ignore", invalid="ignore"):
        product = matrix.conj().T @ matrix
    return float(np.max(np.abs(product - identity)))


def unitary_matrix(matrix: ArrayLike, wire_count: int) -> NDArray[np.complex128]:
    """Check a matrix for the given number of wires and return it as a read-only exact unitary.

    A matrix within UNITARY_TOLERANCE of unitary is replaced by the nearest unitary,
    so applying it many times keeps the state normalized.
    """
    try:
        matrix = np.array(matrix, dtype=np.complex128)
    except (TypeError, ValueError):
        raise ValueError("Matrix entries must be numbers.") from None

    size = 2**wire_count
    if matrix.shape != (size, size):
        raise ValueError(f"A gate on {wire_count} wire(s) needs a {size}×{size} matrix.")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Matrix entries must be finite numbers.")

    error = unitarity_error(matrix)
    # A NaN error fails every comparison, so it is rejected explicitly.
    if not np.isfinite(error) or error > UNITARY_TOLERANCE:
        raise ValueError(f"The matrix must be unitary. U†U differs from the identity by {error:.1e}.")
    if error > _ROUNDING_ERROR:
        # The nearest unitary keeps the singular vectors and sets every singular value to 1.
        left_vectors, _, right_vectors = np.linalg.svd(matrix)
        matrix = left_vectors @ right_vectors

    matrix.setflags(write=False)
    return matrix


def gate_matrix(gate: str | ArrayLike, wire_count: int) -> NDArray[np.complex128]:
    """Resolve a built-in gate name or check a custom matrix for the selected wires."""
    if not isinstance(gate, str):
        return unitary_matrix(gate, wire_count)

    try:
        matrix = _GATES[gate.upper()]
    except KeyError:
        raise ValueError(f"Unknown gate {gate!r}.") from None
    gate_wires = matrix.shape[0].bit_length() - 1
    if gate_wires != wire_count:
        raise ValueError(f"{gate.upper()} acts on {gate_wires} wire(s), not {wire_count}.")
    return matrix

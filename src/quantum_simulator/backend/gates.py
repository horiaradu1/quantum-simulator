"""Gate matrices in computational basis order, with input states as columns.

gate_matrix looks up a built-in gate or validates a user-supplied matrix.
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


def gate_matrix(gate: str | ArrayLike, wire_count: int) -> NDArray[np.complex128]:
    """Resolve a gate name or validate a custom matrix for the selected wires."""
    is_named_gate = isinstance(gate, str)
    if is_named_gate:
        try:
            matrix = _GATES[gate.upper()]
        except KeyError:
            raise ValueError(f"Unknown gate {gate!r}.") from None
    else:
        matrix = np.asarray(gate, dtype=np.complex128)

    size = 2**wire_count
    if matrix.shape != (size, size):
        raise ValueError(f"A gate on {wire_count} wire(s) needs a {size}×{size} matrix.")

    if not is_named_gate:
        # A unitary preserves the state's norm. Its conjugate transpose acts as its inverse.
        conjugate_transpose = matrix.conj().T
        if not np.allclose(conjugate_transpose @ matrix, np.eye(size), rtol=0, atol=1e-8):
            raise ValueError("The gate matrix must be unitary.")
    return matrix

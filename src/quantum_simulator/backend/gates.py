"""Gate matrices in computational basis order, with input states as columns.

gate_matrix looks up a built-in gate or validates a user-supplied matrix.
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
    "CNOT": np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=complex),
    # Reverse CNOT uses the second wire as the control.
    "CNOT10": np.array([
        [1, 0, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
    ], dtype=complex),
    "CH": np.array([
        [1, 0,           0,            0],
        [0, 1,           0,            0],
        [0, 0, 1 / sqrt(2),  1 / sqrt(2)],
        [0, 0, 1 / sqrt(2), -1 / sqrt(2)],
    ], dtype=complex),
    "SWAP": np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], dtype=complex),
    "TOFFOLI": np.array([
        [1, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0],
    ], dtype=complex),
}

_GATES = _SINGLE_QUBIT_GATES | _MULTI_QUBIT_GATES


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

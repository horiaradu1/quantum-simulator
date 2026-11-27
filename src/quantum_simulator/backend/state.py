"""QuantumState applies gates and measures a register.

Outcome describes one basis state's amplitude and probability.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from operator import index

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .gates import gate_matrix


@dataclass(frozen=True, slots=True)
class Outcome:
    """The bitstring, amplitude, and probability of one computational basis state.

    The dataclass generates the constructor and equality from the fields below.
    `frozen=True` makes the fields read-only, and `slots=True` saves memory per row.
    """

    basis: str
    amplitude: complex
    probability: float

    @property
    def magnitude(self) -> float:
        """Compute the absolute value on access. `@property` makes this method read like a field."""
        return abs(self.amplitude)


class QuantumState:
    """An n-qubit state vector with qubit 0 as the leftmost basis bit."""

    def __init__(self, n_qubits: int, *, rng: np.random.Generator | None = None):
        try:
            n_qubits = index(n_qubits)
        except TypeError:
            raise ValueError("The qubit count must be a positive integer.") from None
        if n_qubits < 1:
            raise ValueError("The qubit count must be a positive integer.")

        self._n_qubits = n_qubits
        self._rng = rng if rng is not None else np.random.default_rng()
        self._amplitudes = np.zeros(2**n_qubits, dtype=np.complex128)
        self._amplitudes[0] = 1

    @property
    def n_qubits(self) -> int:
        return self._n_qubits

    @property
    def amplitudes(self) -> NDArray[np.complex128]:
        """Return a copy so an inspection of `state.amplitudes` cannot change the register."""
        return self._amplitudes.copy()

    @property
    def probabilities(self) -> NDArray[np.float64]:
        return np.abs(self._amplitudes) ** 2

    def initialize(self, bits: str | Iterable[int]) -> None:
        """Reset the register to a computational basis state."""
        if not isinstance(bits, str):
            try:
                values = tuple(index(bit) for bit in bits)
            except TypeError:
                raise ValueError("Basis bits must be 0 or 1.") from None
            if any(bit not in (0, 1) for bit in values):
                raise ValueError("Basis bits must be 0 or 1.")
            bits = "".join(str(bit) for bit in values)

        if len(bits) != self.n_qubits or any(bit not in "01" for bit in bits):
            raise ValueError(f"Provide exactly {self.n_qubits} basis bits (0 or 1).")

        amplitudes = np.zeros_like(self._amplitudes)
        amplitudes[int(bits, 2)] = 1
        self._amplitudes = amplitudes

    def apply_gate(self, gate: str | ArrayLike, *qubits: int) -> None:
        """Apply a named gate or unitary matrix in the given wire order.

        CNOT and CH take the control first, CNOT10 takes it second, and
        Toffoli takes both controls before the target.
        """
        gate_wires = self._validate_wires(qubits)
        matrix = gate_matrix(gate, len(gate_wires))

        # One axis per wire lets us index an amplitude by its individual bits.
        # Move the gate's wires to the front in the matrix's bit order.
        amplitudes_by_wire = self._amplitudes.reshape((2,) * self.n_qubits)
        leading_axes = tuple(range(len(gate_wires)))
        gate_wires_first = np.moveaxis(amplitudes_by_wire, gate_wires, leading_axes)

        # Each column fixes the other wires. On q1 of a two-qubit register,
        # the pairs are (|00>, |01>) and (|10>, |11>).
        amplitude_groups = gate_wires_first.reshape(matrix.shape[1], -1)
        updated_groups = np.dot(matrix, amplitude_groups)

        updated_by_wire = updated_groups.reshape(gate_wires_first.shape)
        register_order = np.moveaxis(updated_by_wire, leading_axes, gate_wires)
        self._amplitudes = register_order.reshape(-1)

    def sample(self) -> str:
        """Draw a computational basis label without changing the state."""
        probabilities = self.probabilities
        # Gate arithmetic can introduce rounding drift. The sampler expects a sum of 1.
        probabilities /= probabilities.sum()
        basis_index = self._rng.choice(probabilities.size, p=probabilities)
        return self._basis_label(basis_index)

    def measure(self) -> str:
        """Measure the entire register and collapse it to the returned basis label."""
        basis = self.sample()
        self.initialize(basis)
        return basis

    def outcomes(self) -> Iterator[Outcome]:
        """Yield every computational basis outcome, including zero amplitudes."""
        probabilities = self.probabilities
        for basis_index, amplitude in enumerate(self._amplitudes):
            yield Outcome(
                basis=self._basis_label(basis_index),
                amplitude=complex(amplitude),
                probability=float(probabilities[basis_index]),
            )

    def _validate_wires(self, qubits: tuple[int, ...]) -> tuple[int, ...]:
        try:
            wires = tuple(index(qubit) for qubit in qubits)
        except TypeError:
            raise ValueError("Gate wires must be integer indices.") from None
        if not wires or any(wire < 0 or wire >= self.n_qubits for wire in wires):
            raise ValueError("Gate wires must be within the register.")
        if len(set(wires)) != len(wires):
            raise ValueError("Gate wires must be distinct.")
        return wires

    def _basis_label(self, basis_index: int) -> str:
        return format(basis_index, f"0{self.n_qubits}b")

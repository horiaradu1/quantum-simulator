"""Run a circuit gate by gate and report its final state as plain data."""

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np

from .circuit import FORMAT_VERSION, Circuit, PlacedGate
from .state import QuantumState


@dataclass(frozen=True)
class RunSettings:
    """Options shared by Python, HTTP and saved files. The defaults give an ideal run."""

    seed: int | None = None
    p: float = 0

    def __post_init__(self):
        if self.seed is not None and (type(self.seed) is not int or self.seed < 0):
            raise ValueError("The seed must be a non-negative integer.")
        if self.p != 0:
            raise ValueError("Noise is not available yet, so p must be 0.")

    @classmethod
    def from_dict(cls, settings: object) -> "RunSettings":
        """Read optional settings. Missing settings give an ideal run."""
        if settings is None:
            return cls()
        if not isinstance(settings, dict):
            raise ValueError('"settings" must be an object.')
        return cls(seed=settings.get("seed"), p=settings.get("p", 0))

    def to_dict(self) -> dict:
        return {"seed": self.seed, "p": self.p}


def prepare_state(circuit: Circuit, settings: RunSettings | None = None) -> QuantumState:
    """Create the register in the circuit's initial basis state."""
    if settings is None:
        settings = RunSettings()
    state = QuantumState(circuit.qubits, rng=np.random.default_rng(settings.seed))
    state.initialize(circuit.initial_bits)
    return state


def apply_gates(state: QuantumState, circuit: Circuit) -> Iterator[PlacedGate]:
    """Apply the circuit's gates in execution order, yielding each placed gate after it runs.

    A gate from a circuit or a controlled gate runs as its smaller matrices, but still counts as one gate.
    """
    library = circuit.gate_library()
    for gate in circuit.execution_order():
        for operation in library.matrix_operations(gate.name, gate.wires):
            state.apply_gate(operation.matrix, *operation.targets, controls=operation.controls)
        yield gate


def run(circuit: Circuit, settings: RunSettings | None = None) -> QuantumState:
    """Run the whole circuit and return its final state at full precision."""
    state = prepare_state(circuit, settings)
    for _ in apply_gates(state, circuit):
        pass
    return state


def state_to_dict(state: QuantumState) -> dict:
    """List every basis state with its amplitude as [real, imaginary] and its probability."""
    outcomes = []
    for outcome in state.outcomes():
        outcomes.append({
            "basis": outcome.basis,
            "amplitude": [outcome.amplitude.real, outcome.amplitude.imag],
            "probability": outcome.probability,
        })
    return {"kind": "state", "version": FORMAT_VERSION, "qubits": state.n_qubits, "outcomes": outcomes}

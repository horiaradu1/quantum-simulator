# Quantum simulator

An Introduction to Quantum Computing team project to build a quantum circuit simulator.

- [Assignment PDF](docs/assignment/IQC_QuantumSimulatorTasks.pdf)
- [Lab 2 reference materials](docs/references/README.md)

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) using its standalone installer or a package manager. No separate Python installation is required.

From the repository root, run:

```sh
uv sync --locked
uv run --locked python -c "import quantum_simulator"
```

`uv sync --locked` downloads the Python version pinned in `.python-version` if needed, creates a local `.venv`, and installs the project and its dependencies using `uv.lock`. The second command checks that the package imports successfully. No output is expected.

## Desktop app

```sh
uv run --locked python -m quantum_simulator
```

- Set the qubit count and initial bits. Drag gates onto the circuit or select a gate and click a cell. Right-click to remove a gate.
- **Run** shows amplitudes and probabilities. **Measure** collapses the state to one outcome.
- Use **File** to start a circuit, open a saved circuit or try an example. **Save** (Ctrl+S) writes the open circuit or gate to its current file. **Save As…** lets you choose a new path.
- Under **Gates**, enter a matrix for 1–3 qubits, add a control to a gate or turn the current circuit into a gate. **Create** adds it to the palette. **Create and save…** also writes a gate file.
- Use **Manage gates** to inspect gates, save a custom gate to its own file or delete an unused gate.
- **File → Open gate** loads gates into the palette. Gates made from circuits also open for editing. Circuit and gate files include the custom gates they use.

## Python API

The desktop app and the HTTP server use the same call. Basis labels put `q0` on the left.

```python
from quantum_simulator import Circuit, PlacedGate, run

# PlacedGate(column, gate ID, wires in gate order)
bell = Circuit(2, "00", (PlacedGate(0, "H", (0,)), PlacedGate(1, "CNOT", (0, 1))))
state = run(bell)
for outcome in state.outcomes():
    print(outcome.basis, outcome.amplitude, outcome.probability)
```

`run(circuit, settings)` also accepts `RunSettings(seed=...)` with a non-negative integer seed. Noise (`p`) must be 0 until it is implemented.

Pass `MatrixGate`, `ControlledGate` or `CircuitGate` objects to `Circuit` through its `definitions` argument.

## HTTP server

```sh
uv run --locked python -m quantum_simulator.server --port 8000
```

POST a circuit document to `/simulate` with a `Content-Length` header. The server accepts JSON bodies up to 1 MiB and returns HTTP 413 for larger requests. The optional `settings` object takes `seed` and `p`.

```json
{
  "kind": "circuit",
  "version": 1,
  "qubits": 2,
  "initial_bits": "00",
  "columns": [
    [{"gate": "H", "wires": [0]}],
    [{"gate": "CNOT", "wires": [0, 1]}]
  ]
}
```

List custom gates in `definitions`. Matrix entries use `[real, imaginary]`. Gates from circuits use `"kind": "circuit_gate"` and list their operations in order, e.g. `{"gate": "H", "wires": [0]}` for H on the first local wire.

The response lists every basis state with its amplitude as `[real, imaginary]` and its probability. An invalid circuit returns status 400 with an `error` message. The server listens on `127.0.0.1` and allows requests from any browser origin.

## Tests

From the repository root, run the checklist runner:

```sh
uv run --locked python -X utf8 tests/run_tests.py
```

The terminal checklist and [test report](tests/test_results.md) group results by suite and then by file. The report links to each test and includes tracebacks for failures.

| Suite | What it checks | Run separately |
|---|---|---|
| [Quantum tests](tests/quantum/) | Gates, circuit equivalences, states and measurement | `uv run --locked python -m unittest discover -s tests/quantum -v` |
| [Application tests](tests/application/) | Validation, file handling, editor, HTTP API and GUI | `uv run --locked python -m unittest discover -s tests/application -v` |

To run both directly with unittest, use `uv run --locked python -m unittest discover -s tests -v`.

## Project layout

- `src/quantum_simulator/backend/` — simulation, gates, circuit editing and file handling
- `src/quantum_simulator/gui/` — desktop app
- `src/quantum_simulator/server.py` — HTTP server
- `src/quantum_simulator/resources/` — example circuits and images
- `tests/` — [test suites and runner](#tests)
- `data/circuits/` — locally saved circuits
- `data/gates/` — saved gates
- `pyproject.toml` — package configuration and dependency declarations


## Python tooling (TBD)

We use `uv` so the team can set up the pinned Python version and locked
dependencies with `uv sync --locked`.

Other common workflows include `pip` + `venv` for package installation
and isolation, Poetry for dependency locking and packaging, and Conda
for environments that also need non-Python libraries.

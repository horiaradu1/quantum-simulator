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

Choose 1–12 qubits. Use the initial-state arrows to step through binary values or type one `0` or `1` per qubit. Drag a gate from the palette onto a circuit cell. To place a multi-wire gate, click each remaining wire in the same column or drop the same gate on each wire. For controlled gates, choose the controls before the target. Right-click a gate to remove it.

**Run** starts from the selected initial state and shows the nonzero outcomes below the circuit. **Measure** collapses the current result to a single outcome.

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

`run(circuit, settings)` also accepts `RunSettings(seed=...)`. Noise (`p`) must be 0 until it is implemented.

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

The response lists every basis state with its amplitude as `[real, imaginary]` and its probability. An invalid circuit returns status 400 with an `error` message. The server listens on `127.0.0.1` and allows requests from any browser origin.

## Tests

From the repository root, run the checklist runner:

```sh
uv run --locked python -X utf8 tests/run_tests.py
```

The terminal checklist and [test report](tests/test_results.md) group results by suite and then by file. The report links to each test and includes tracebacks for failures.

| Suite | What it checks | Run separately |
|---|---|---|
| [Quantum tests](tests/quantum/) | Gate matrices, circuit equivalences, expected amplitudes and probabilities, initialization, and measurement | `uv run --locked python -m unittest discover -s tests/quantum -v` |
| [Application tests](tests/application/) | Input validation, circuit data and execution order, editor behavior, HTTP responses, and Qt workflows | `uv run --locked python -m unittest discover -s tests/application -v` |

To run both directly with unittest, use `uv run --locked python -m unittest discover -s tests -v`.

## Project layout

- `src/quantum_simulator/backend/` — Qt-free simulator code:
  - `gates.py` gate matrices, and `gate_catalog.py` palette and drawing details
  - `state.py` state simulation, `circuit.py` circuits and the circuit format, and `runner.py` runs and results
  - `editor.py` editing rules shared by frontends
- `src/quantum_simulator/server.py` — HTTP server for `POST /simulate`
- `src/quantum_simulator/gui/` — desktop window and circuit drawing
- `tests/` — [test suites and checklist runner](#tests)
- `pyproject.toml` — package configuration and dependency declarations


## Python tooling (TBD)

We use `uv` so the team can set up the pinned Python version and locked
dependencies with `uv sync --locked`.

Other common workflows include `pip` + `venv` for package installation
and isolation, Poetry for dependency locking and packaging, and Conda
for environments that also need non-Python libraries.

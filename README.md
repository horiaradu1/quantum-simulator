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

## Tests

From the repository root, run the checklist runner:

```sh
uv run --locked python -X utf8 tests/run_tests.py
```

It prints a checklist and writes the latest results to [`tests/test_results.md`](tests/test_results.md). The checklist starts with gate properties, individual gates, circuit equivalences, and known circuit results, in that order. The report groups tests by file, links to their source, and includes tracebacks for failures. You can also run the suite directly with `uv run --locked python -m unittest discover -s tests -v`.

## Project layout

- `src/quantum_simulator/backend/` — gate matrices in `gates.py` and state simulation in `state.py`
- `src/quantum_simulator/gui/` — desktop window and circuit drawing
- `tests/` — gate, circuit, measurement, and state tests, plus the checklist runner
- `pyproject.toml` — package configuration and dependency declarations


## Python tooling (TBD)

We use `uv` so the team can set up the pinned Python version and locked
dependencies with `uv sync --locked`.

Other common workflows include `pip` + `venv` for package installation
and isolation, Poetry for dependency locking and packaging, and Conda
for environments that also need non-Python libraries.

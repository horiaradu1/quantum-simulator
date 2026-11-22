# Quantum simulator

An Introduction to Quantum Computing team project to build a quantum circuit simulator.

- [Assignment PDF](docs/assignment/IQC_QuantumSimulatorTasks.pdf)
- [Assignment task tracker](docs/tasks.md)
- [Lab 2 reference materials](docs/references/README.md)

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) using its standalone installer or a package manager. No separate Python installation is required.

From the repository root, run:

```sh
uv sync --locked
uv run --locked python -c "import quantum_simulator"
```

`uv sync --locked` downloads the Python version pinned in `.python-version` if needed, creates a local `.venv`, and installs the project and its dependencies using `uv.lock`. The second command checks that the package imports successfully. No output is expected.

## Project layout

- `src/quantum_simulator/` — simulator code
- `tests/` — tests
- `pyproject.toml` — package configuration and dependency declarations


## Python tooling

We use `uv` so the team can set up the pinned Python version and locked
dependencies with `uv sync --locked`.

Other common workflows include `pip` + `venv` for package installation
and isolation, Poetry for dependency locking and packaging, and Conda
for environments that also need non-Python libraries.
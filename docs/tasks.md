# Assignment

## AI use

You may use AI to develop the simulator if you understand the code. The team must create the presentation without AI (p. 4).

## Simulator conventions

The register starts in `|00…0⟩`. Basis labels put `q0` on the left. Gate calls list wires in matrix order. Controlled gates such as CNOT, CH and CY take the control first, CNOT10 takes it second, and Toffoli takes both controls before the target.

The simulator returns fixed-width basis labels from `sample()` and `measure()`. Sampling preserves the state. Measurement collapses the full register. `outcomes()` supplies basis labels, complex amplitudes, and probabilities for display.

## TLDR

* PPT, prezentare feature map , 
* ⁠how much is covered , 
* ⁠the code / GitHub , 
* ⁠tine o ora , 
* ⁠trb sa vorbească toti , 
* ⁠se face live presentation , 
* ⁠întrebări din sală , 
* ⁠cele mai mare challenge uri , 
* ⁠ce a făcut fiecare membru , 
* ⁠aceasta arhiva trb trimisă înainte sau in ziua prezentării


## Assignment Tasks

[Assignment PDF](assignment/IQC_QuantumSimulatorTasks.pdf)

✅ Complete · ⚪ To do

### A. Minimal implementation (mandatory - from lab)

- ✅ Support for N-qubit states · `QuantumState` in [state.py](../src/quantum_simulator/backend/state.py)
- ✅ Support for state initialization (by attributing a 0/1 value to each qubit) · `QuantumState.initialize()` in [state.py](../src/quantum_simulator/backend/state.py)
- ✅ Single-qubit gates implementation: H, X, S · `_SINGLE_QUBIT_GATES` in [gates.py](../src/quantum_simulator/backend/gates.py)
- ✅ Multi-qubit gates implementation: CNOT, CH, SWAP, TOFFOLI · `_MULTI_QUBIT_GATES` and `_CONTROLLED_GATES` in [gates.py](../src/quantum_simulator/backend/gates.py)
- ✅ State amplitudes calculation and display · `QuantumState.apply_gate()` in [state.py](../src/quantum_simulator/backend/state.py) and `SimulatorWindow._display_results()` in [window.py](../src/quantum_simulator/gui/window.py)
- ✅ Measurement · `QuantumState.sample()` and `QuantumState.measure()` in [state.py](../src/quantum_simulator/backend/state.py)

### B. Minor tasks (0.5p)

- ✅ Add the following gates: Y, Z, T, CY, CZ, CT, CS · `_SINGLE_QUBIT_GATES` and `_CONTROLLED_GATES` in [gates.py](../src/quantum_simulator/backend/gates.py)
- ✅ Support for user-defined gates given in matrix form · `MatrixGate` and `GateLibrary` in [gate_library.py](../src/quantum_simulator/backend/gate_library.py), dialog in [gate_dialogs.py](../src/quantum_simulator/gui/gate_dialogs.py)
- ✅ Support for user-defined gates given as series of other defined gates · `CircuitGate` in [gate_library.py](../src/quantum_simulator/backend/gate_library.py)
- ✅ Support for Controlled-U gate (where U is any already defined gate) · `ControlledGate` in [gate_library.py](../src/quantum_simulator/backend/gate_library.py)
- ✅ Support for user-defined gates export and import · [gate_file.py](../src/quantum_simulator/backend/gate_file.py)
- ✅ Allow controlled gates to have the control and the target on any of the N qubit (not necessarily adjacent) · `QuantumState.apply_gate()` in [state.py](../src/quantum_simulator/backend/state.py)
- ⚪ Allow measurement to be applied to any of the N qubits (not necessarily on the entire state)
- ✅ Support for circuit export and import · [circuit_file.py](../src/quantum_simulator/backend/circuit_file.py)
- ⚪ Support for computing the density matrix of a given state
- ⚪ Add ability to measure in +/- basis
- ⚪ Add ability to simulate quantum noise: random bit-flip (X gate) and random phase-flip (Z gate) for each qubit after each gate applied, with probability p (configurable)
- ⚪ Add ability to compute the quantum fidelity between two states

#### Check your own code with the following:

- ⚪ H followed by H should restore the state
- ⚪ A phase-sensitive circuit should give the expected result
- ⚪ Bell-state preparation should give the correct joint probabilities
- ⚪ Reversing a CNOT’s control and target should change the appropriate inputs
- ⚪ Non-adjacent operations should act on the intended wires
- ⚪ Repeated measurements one after another in the same basis should return the same outcome
- ⚪ Measuring one qubit of a Bell pair should produce the correct conditional state
- ⚪ A saved and reloaded circuit should behave identically
- ⚪ A state and its globally phase-shifted version should have fidelity one

### C. Major tasks (2p) – pick at least 4 major tasks

#### 1. Interactive circuit GUI and debugger

- ⚪ Package the simulator as a desktop or web application with a graphical user interface
- ⚪ Allow the user to create and edit circuits, configure operations and run simulations using buttons and drag-and-drop interactions
- ⚪ Represent circuits, state amplitudes, qubit states and measurement results visually
- ⚪ Implement a circuit debugger that allows the user to step through operations and inspect intermediate states
- ⚪ Allow the debugger to record measurement outcomes, reproduce runs and evaluate user-defined assertions

#### 2. Integrations

- ⚪ Implement circuit export to at least three of the following: Qiskit, TKET, Cirq, Q#, PyQuil
- ⚪ Allow circuits to be executed using each of the integrated tools and display the returned results
- ⚪ Add support for configuring the API keys and connection settings required to access IBM quantum hardware
- ⚪ Allow the user to select an available IBM quantum device, submit a circuit for execution and retrieve its results

#### 6. Quantum noise and error correction

- ⚪ Add the ability to simulate bit-flip, phase-flip, depolarizing and amplitude-damping noise with configurable probabilities
- ⚪ Allow noise to be assigned to specific qubits and gates, with a clearly defined rule for when it is applied
- ⚪ Simulate noisy evolution using density matrices or repeated stochastic trajectories, and collect averaged output statistics
- ⚪ Implement the three-qubit bit-flip and phase-flip correction codes, including encoding, syndrome extraction, correction and decoding
- ⚪ Compare protected and unprotected circuits at different noise levels, using arbitrary input states, and demonstrate which errors each code can and cannot correct

#### 7. Quantum algorithms and oracle construction

- ⚪ Implement configurable circuit generators for the Deutsch–Jozsa, Bernstein–Vazirani and Grover algorithms
- ⚪ Allow the user to define Boolean functions through truth tables or Boolean expressions, and generate the corresponding reversible or phase oracles
- ⚪ Allow algorithm parameters to be configured, including register size, hidden strings, marked states and the number of Grover iterations
- ⚪ Display the generated circuits, number of oracle calls and probabilities of obtaining the expected results
- ⚪ Provide experiments with different inputs and parameters, comparing the simulated results with theoretical predictions and demonstrating cases where an algorithm’s assumptions are not satisfied

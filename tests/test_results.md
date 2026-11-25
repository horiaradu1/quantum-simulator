# Test results

**✅ Passed** · 39 tests run

## Gate properties

- ✅ **[Every built-in gate is unitary.](test_gate_properties.py#L14)**
  - ✅ [`(gate='X')`](test_gate_properties.py#L14)
  - ✅ [`(gate='Y')`](test_gate_properties.py#L14)
  - ✅ [`(gate='Z')`](test_gate_properties.py#L14)
  - ✅ [`(gate='H')`](test_gate_properties.py#L14)
  - ✅ [`(gate='S')`](test_gate_properties.py#L14)
  - ✅ [`(gate='T')`](test_gate_properties.py#L14)
  - ✅ [`(gate='CNOT')`](test_gate_properties.py#L14)
  - ✅ [`(gate='CNOT10')`](test_gate_properties.py#L14)
  - ✅ [`(gate='CH')`](test_gate_properties.py#L14)
  - ✅ [`(gate='SWAP')`](test_gate_properties.py#L14)
  - ✅ [`(gate='TOFFOLI')`](test_gate_properties.py#L14)
- ✅ **[All built-in gates except S and T are Hermitian.](test_gate_properties.py#L23)**
  - ✅ [`(gate='H')`](test_gate_properties.py#L23)
  - ✅ [`(gate='X')`](test_gate_properties.py#L23)
  - ✅ [`(gate='Y')`](test_gate_properties.py#L23)
  - ✅ [`(gate='Z')`](test_gate_properties.py#L23)
  - ✅ [`(gate='CNOT')`](test_gate_properties.py#L23)
  - ✅ [`(gate='CNOT10')`](test_gate_properties.py#L23)
  - ✅ [`(gate='CH')`](test_gate_properties.py#L23)
  - ✅ [`(gate='SWAP')`](test_gate_properties.py#L23)
  - ✅ [`(gate='TOFFOLI')`](test_gate_properties.py#L23)
  - ✅ [`(gate='S')`](test_gate_properties.py#L23)
  - ✅ [`(gate='T')`](test_gate_properties.py#L23)

## Gates

- ✅ **[H gate.](test_gates.py#L30)**
  - ✅ [`(input='0')`](test_gates.py#L30)
  - ✅ [`(input='1')`](test_gates.py#L30)
- ✅ **[S gate.](test_gates.py#L38)**
  - ✅ [`(input='0')`](test_gates.py#L38)
  - ✅ [`(input='1')`](test_gates.py#L38)
- ✅ **[T gate.](test_gates.py#L45)**
  - ✅ [`(input='0')`](test_gates.py#L45)
  - ✅ [`(input='1')`](test_gates.py#L45)
- ✅ **[X gate.](test_gates.py#L52)**
  - ✅ [`(input='0')`](test_gates.py#L52)
  - ✅ [`(input='1')`](test_gates.py#L52)
- ✅ **[X and Y on a superposition.](test_gates.py#L73)**
  - ✅ [`(gate='X')`](test_gates.py#L73)
  - ✅ [`(gate='Y')`](test_gates.py#L73)
- ✅ **[Y gate.](test_gates.py#L59)**
  - ✅ [`(input='0')`](test_gates.py#L59)
  - ✅ [`(input='1')`](test_gates.py#L59)
- ✅ **[Z gate.](test_gates.py#L66)**
  - ✅ [`(input='0')`](test_gates.py#L66)
  - ✅ [`(input='1')`](test_gates.py#L66)
- ✅ **[Controlled-H gate.](test_gates.py#L87)**
  - ✅ [`(input='00')`](test_gates.py#L87)
  - ✅ [`(input='01')`](test_gates.py#L87)
  - ✅ [`(input='10')`](test_gates.py#L87)
  - ✅ [`(input='11')`](test_gates.py#L87)
- ✅ **[CNOT truth table.](test_gates.py#L97)**
  - ✅ [`(input='00')`](test_gates.py#L97)
  - ✅ [`(input='01')`](test_gates.py#L97)
  - ✅ [`(input='10')`](test_gates.py#L97)
  - ✅ [`(input='11')`](test_gates.py#L97)
- ✅ **[Reverse CNOT truth table.](test_gates.py#L101)**
  - ✅ [`(input='00')`](test_gates.py#L101)
  - ✅ [`(input='01')`](test_gates.py#L101)
  - ✅ [`(input='10')`](test_gates.py#L101)
  - ✅ [`(input='11')`](test_gates.py#L101)
- ✅ **[SWAP truth table.](test_gates.py#L105)**
  - ✅ [`(input='00')`](test_gates.py#L105)
  - ✅ [`(input='01')`](test_gates.py#L105)
  - ✅ [`(input='10')`](test_gates.py#L105)
  - ✅ [`(input='11')`](test_gates.py#L105)
- ✅ **[Toffoli truth table.](test_gates.py#L109)**
  - ✅ [`(input='000')`](test_gates.py#L109)
  - ✅ [`(input='001')`](test_gates.py#L109)
  - ✅ [`(input='010')`](test_gates.py#L109)
  - ✅ [`(input='011')`](test_gates.py#L109)
  - ✅ [`(input='100')`](test_gates.py#L109)
  - ✅ [`(input='101')`](test_gates.py#L109)
  - ✅ [`(input='110')`](test_gates.py#L109)
  - ✅ [`(input='111')`](test_gates.py#L109)
- ✅ **[Invalid gates leave the state intact.](test_gates.py#L134)**
  - ✅ [`(gate='missing', wires=(0,))`](test_gates.py#L134)
  - ✅ [`(gate='H', wires=())`](test_gates.py#L134)
  - ✅ [`(gate='H', wires=(-1,))`](test_gates.py#L134)
  - ✅ [`(gate='X', wires=(2,))`](test_gates.py#L134)
  - ✅ [`(gate='CNOT', wires=(0,))`](test_gates.py#L134)
  - ✅ [`(gate='CNOT', wires=(0, 0))`](test_gates.py#L134)
  - ✅ [`(gate=[[1, 0], [0, 1]], wires=(0, 1))`](test_gates.py#L134)
  - ✅ [`(gate=[[0.5, 0.5], [0.5, 0.5]], wires=(0,))`](test_gates.py#L134)
  - ✅ [`(gate=[[5, 4], [3, 7]], wires=(0,))`](test_gates.py#L134)
- ✅ **[Reversed and nonadjacent wires.](test_gates.py#L113)**
  - ✅ [`(gate='CNOT', wires=(3, 0), input='0001')`](test_gates.py#L113)
  - ✅ [`(gate='CNOT', wires=(3, 0), input='1000')`](test_gates.py#L113)
  - ✅ [`(gate='CNOT10', wires=(0, 2), input='0010')`](test_gates.py#L113)
  - ✅ [`(gate='SWAP', wires=(2, 0), input='0011')`](test_gates.py#L113)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='1101')`](test_gates.py#L113)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='1100')`](test_gates.py#L113)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='0101')`](test_gates.py#L113)

## Circuit equivalences

- ✅ **[Gates on disjoint wires commute.](test_circuit_equivalences.py#L56)**
- ✅ **[H, X, H gives Z.](test_circuit_equivalences.py#L32)**
- ✅ **[Two Hadamards restore the state.](test_circuit_equivalences.py#L36)**
- ✅ **[T squared gives S and S squared gives Z.](test_circuit_equivalences.py#L26)**
  - ✅ [`(gate='T')`](test_circuit_equivalences.py#L26)
  - ✅ [`(gate='S')`](test_circuit_equivalences.py#L26)
- ✅ **[Reverse CNOT matches CNOT with swapped wires.](test_circuit_equivalences.py#L47)**
- ✅ **[Three alternating CNOTs implement SWAP.](test_circuit_equivalences.py#L51)**

## Circuit results

- ✅ **[Bell-state results.](test_circuit_results.py#L15)**
- ✅ **[Four-qubit circuit results.](test_circuit_results.py#L34)**

## Measurement

- ✅ **[Computational-basis measurement.](test_measurement.py#L20)**
  - ✅ [`(basis='0')`](test_measurement.py#L20)
  - ✅ [`(basis='1')`](test_measurement.py#L20)
- ✅ **[Measure in the ± basis using H.](test_measurement.py#L36)**
  - ✅ [`(basis='0')`](test_measurement.py#L36)
  - ✅ [`(basis='1')`](test_measurement.py#L36)
- ✅ **[Sampling preserves the state.](test_measurement.py#L52)**
- ✅ **[Five-qubit measurement collapse.](test_measurement.py#L64)**

## State

- ✅ **[Initialization preserves bit order.](test_state.py#L25)**
  - ✅ [`(bits='100')`](test_state.py#L25)
  - ✅ [`(bits='001')`](test_state.py#L25)
  - ✅ [`(bits='01100')`](test_state.py#L25)
- ✅ **[Invalid qubit counts and bits.](test_state.py#L41)**
  - ✅ [`(count=0)`](test_state.py#L41)
  - ✅ [`(count=-1)`](test_state.py#L41)
  - ✅ [`(count=2.5)`](test_state.py#L41)
  - ✅ [`(bits='0')`](test_state.py#L41)
  - ✅ [`(bits='000')`](test_state.py#L41)
  - ✅ [`(bits='0x')`](test_state.py#L41)
  - ✅ [`(bits=[0, 2])`](test_state.py#L41)
  - ✅ [`(bits=[0, 0.5])`](test_state.py#L41)
- ✅ **[New registers start at zero.](test_state.py#L20)**
- ✅ **[Reinitialization clears the previous state.](test_state.py#L34)**

## Technical

- ✅ **[Closing during a run discards unfinished results.](test_technical.py#L122)**
- ✅ **[A failed run returns to the editor and can be retried.](test_technical.py#L109)**
- ✅ **[Run shows loading, then the Bell pair can be measured.](test_technical.py#L88)**
- ✅ **[Choosing a new column restarts Toffoli at its first control.](test_technical.py#L65)**
- ✅ **[A CNOT keeps its control after a duplicate or blocked target.](test_technical.py#L46)**
- ✅ **[Disposing of a busy window destroys its timer.](test_technical.py#L159)**
- ✅ **[Rerunning and clearing release previous states.](test_technical.py#L137)**

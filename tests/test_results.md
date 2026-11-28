# Test results

**✅ Passed** · 95 tests run

## Quantum tests

### Gate properties

- ✅ **[Every built-in gate is unitary.](quantum/test_gate_properties.py#L14)**
  - ✅ [`(gate='X')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='Y')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='Z')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='H')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='S')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='T')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CNOT10')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='SWAP')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CNOT')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CH')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CY')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CZ')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CS')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='CT')`](quantum/test_gate_properties.py#L14)
  - ✅ [`(gate='TOFFOLI')`](quantum/test_gate_properties.py#L14)
- ✅ **[All built-in gates except S, T, CS and CT are Hermitian.](quantum/test_gate_properties.py#L23)**
  - ✅ [`(gate='H')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='X')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='Y')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='Z')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CNOT')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CNOT10')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CH')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CY')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CZ')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='SWAP')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='TOFFOLI')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='S')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='T')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CS')`](quantum/test_gate_properties.py#L23)
  - ✅ [`(gate='CT')`](quantum/test_gate_properties.py#L23)

### Gates

- ✅ **[H gate.](quantum/test_gates.py#L30)**
  - ✅ [`(input='0')`](quantum/test_gates.py#L30)
  - ✅ [`(input='1')`](quantum/test_gates.py#L30)
- ✅ **[S gate.](quantum/test_gates.py#L38)**
  - ✅ [`(input='0')`](quantum/test_gates.py#L38)
  - ✅ [`(input='1')`](quantum/test_gates.py#L38)
- ✅ **[T gate.](quantum/test_gates.py#L45)**
  - ✅ [`(input='0')`](quantum/test_gates.py#L45)
  - ✅ [`(input='1')`](quantum/test_gates.py#L45)
- ✅ **[X gate.](quantum/test_gates.py#L52)**
  - ✅ [`(input='0')`](quantum/test_gates.py#L52)
  - ✅ [`(input='1')`](quantum/test_gates.py#L52)
- ✅ **[X and Y on a superposition.](quantum/test_gates.py#L73)**
  - ✅ [`(gate='X')`](quantum/test_gates.py#L73)
  - ✅ [`(gate='Y')`](quantum/test_gates.py#L73)
- ✅ **[Y gate.](quantum/test_gates.py#L59)**
  - ✅ [`(input='0')`](quantum/test_gates.py#L59)
  - ✅ [`(input='1')`](quantum/test_gates.py#L59)
- ✅ **[Z gate.](quantum/test_gates.py#L66)**
  - ✅ [`(input='0')`](quantum/test_gates.py#L66)
  - ✅ [`(input='1')`](quantum/test_gates.py#L66)
- ✅ **[Controlled-H gate.](quantum/test_gates.py#L87)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L87)
  - ✅ [`(input='01')`](quantum/test_gates.py#L87)
  - ✅ [`(input='10')`](quantum/test_gates.py#L87)
  - ✅ [`(input='11')`](quantum/test_gates.py#L87)
- ✅ **[CNOT truth table.](quantum/test_gates.py#L149)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L149)
  - ✅ [`(input='01')`](quantum/test_gates.py#L149)
  - ✅ [`(input='10')`](quantum/test_gates.py#L149)
  - ✅ [`(input='11')`](quantum/test_gates.py#L149)
- ✅ **[Reverse CNOT truth table.](quantum/test_gates.py#L153)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L153)
  - ✅ [`(input='01')`](quantum/test_gates.py#L153)
  - ✅ [`(input='10')`](quantum/test_gates.py#L153)
  - ✅ [`(input='11')`](quantum/test_gates.py#L153)
- ✅ **[With the control in |+> and the target in |1>, only the control-1 branch changes.](quantum/test_gates.py#L133)**
  - ✅ [`(gate='CY')`](quantum/test_gates.py#L133)
  - ✅ [`(gate='CZ')`](quantum/test_gates.py#L133)
  - ✅ [`(gate='CS')`](quantum/test_gates.py#L133)
  - ✅ [`(gate='CT')`](quantum/test_gates.py#L133)
- ✅ **[CS multiplies the amplitude of 11 by i.](quantum/test_gates.py#L115)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L115)
  - ✅ [`(input='01')`](quantum/test_gates.py#L115)
  - ✅ [`(input='10')`](quantum/test_gates.py#L115)
  - ✅ [`(input='11')`](quantum/test_gates.py#L115)
- ✅ **[CT multiplies the amplitude of 11 by e^(iπ/4).](quantum/test_gates.py#L124)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L124)
  - ✅ [`(input='01')`](quantum/test_gates.py#L124)
  - ✅ [`(input='10')`](quantum/test_gates.py#L124)
  - ✅ [`(input='11')`](quantum/test_gates.py#L124)
- ✅ **[CY applies Y to the target only when the control is 1.](quantum/test_gates.py#L97)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L97)
  - ✅ [`(input='01')`](quantum/test_gates.py#L97)
  - ✅ [`(input='10')`](quantum/test_gates.py#L97)
  - ✅ [`(input='11')`](quantum/test_gates.py#L97)
- ✅ **[CZ negates the amplitude of 11 and leaves the other inputs unchanged.](quantum/test_gates.py#L106)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L106)
  - ✅ [`(input='01')`](quantum/test_gates.py#L106)
  - ✅ [`(input='10')`](quantum/test_gates.py#L106)
  - ✅ [`(input='11')`](quantum/test_gates.py#L106)
- ✅ **[SWAP truth table.](quantum/test_gates.py#L157)**
  - ✅ [`(input='00')`](quantum/test_gates.py#L157)
  - ✅ [`(input='01')`](quantum/test_gates.py#L157)
  - ✅ [`(input='10')`](quantum/test_gates.py#L157)
  - ✅ [`(input='11')`](quantum/test_gates.py#L157)
- ✅ **[Toffoli truth table.](quantum/test_gates.py#L161)**
  - ✅ [`(input='000')`](quantum/test_gates.py#L161)
  - ✅ [`(input='001')`](quantum/test_gates.py#L161)
  - ✅ [`(input='010')`](quantum/test_gates.py#L161)
  - ✅ [`(input='011')`](quantum/test_gates.py#L161)
  - ✅ [`(input='100')`](quantum/test_gates.py#L161)
  - ✅ [`(input='101')`](quantum/test_gates.py#L161)
  - ✅ [`(input='110')`](quantum/test_gates.py#L161)
  - ✅ [`(input='111')`](quantum/test_gates.py#L161)
- ✅ **[X with control wires, as a tuple or a NumPy array, flips the target only when every control is 1.](quantum/test_gates.py#L165)**
  - ✅ [`(controls=(0,), input='000')`](quantum/test_gates.py#L165)
  - ✅ [`(controls=array([0]), input='000')`](quantum/test_gates.py#L165)
  - ✅ [`(controls=array([0]), input='100')`](quantum/test_gates.py#L165)
  - ✅ [`(controls=array([2, 0]), input='100')`](quantum/test_gates.py#L165)
  - ✅ [`(controls=array([2, 0]), input='101')`](quantum/test_gates.py#L165)
- ✅ **[Reversed and nonadjacent wires.](quantum/test_gates.py#L184)**
  - ✅ [`(gate='CNOT', wires=(3, 0), input='0001')`](quantum/test_gates.py#L184)
  - ✅ [`(gate='CNOT', wires=(3, 0), input='1000')`](quantum/test_gates.py#L184)
  - ✅ [`(gate='CNOT10', wires=(0, 2), input='0010')`](quantum/test_gates.py#L184)
  - ✅ [`(gate='SWAP', wires=(2, 0), input='0011')`](quantum/test_gates.py#L184)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='1101')`](quantum/test_gates.py#L184)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='1100')`](quantum/test_gates.py#L184)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='0101')`](quantum/test_gates.py#L184)

### Circuit equivalences

- ✅ **[CT twice gives CS and CS twice gives CZ on reversed, nonadjacent wires.](quantum/test_circuit_equivalences.py#L32)**
  - ✅ [`(gate='CT')`](quantum/test_circuit_equivalences.py#L32)
  - ✅ [`(gate='CS')`](quantum/test_circuit_equivalences.py#L32)
- ✅ **[Gates on disjoint wires commute.](quantum/test_circuit_equivalences.py#L62)**
- ✅ **[H, X, H gives Z.](quantum/test_circuit_equivalences.py#L38)**
- ✅ **[Two Hadamards restore the state.](quantum/test_circuit_equivalences.py#L42)**
- ✅ **[T squared gives S and S squared gives Z.](quantum/test_circuit_equivalences.py#L26)**
  - ✅ [`(gate='T')`](quantum/test_circuit_equivalences.py#L26)
  - ✅ [`(gate='S')`](quantum/test_circuit_equivalences.py#L26)
- ✅ **[Reverse CNOT matches CNOT with swapped wires.](quantum/test_circuit_equivalences.py#L53)**
- ✅ **[Three alternating CNOTs implement SWAP.](quantum/test_circuit_equivalences.py#L57)**

### Circuit results

- ✅ **[Bell-state results.](quantum/test_circuit_results.py#L15)**
- ✅ **[Four-qubit circuit results.](quantum/test_circuit_results.py#L29)**

### Circuit gates

- ✅ **[A Bell gate from a circuit on q3 and q1 gives 1/√2 at 0000 and 0101 and nothing else.](quantum/test_circuit_gates.py#L28)**
- ✅ **[One control added before CNOT gives Toffoli's matrix, with both controls before the target.](quantum/test_circuit_gates.py#L60)**
- ✅ **[Controlling a nested gate from a circuit equals controlling each of its operations, with the control in superposition.](quantum/test_circuit_gates.py#L36)**

### Measurement

- ✅ **[Computational-basis measurement.](quantum/test_measurement.py#L20)**
  - ✅ [`(basis='0')`](quantum/test_measurement.py#L20)
  - ✅ [`(basis='1')`](quantum/test_measurement.py#L20)
- ✅ **[Measure in the ± basis using H.](quantum/test_measurement.py#L36)**
  - ✅ [`(basis='0')`](quantum/test_measurement.py#L36)
  - ✅ [`(basis='1')`](quantum/test_measurement.py#L36)
- ✅ **[Sampling preserves the state.](quantum/test_measurement.py#L52)**
- ✅ **[Five-qubit measurement collapse.](quantum/test_measurement.py#L64)**

### State

- ✅ **[Initialization preserves bit order.](quantum/test_state.py#L25)**
  - ✅ [`(bits='100')`](quantum/test_state.py#L25)
  - ✅ [`(bits='001')`](quantum/test_state.py#L25)
  - ✅ [`(bits='01100')`](quantum/test_state.py#L25)
- ✅ **[New registers start at zero.](quantum/test_state.py#L20)**
- ✅ **[Reinitialization clears the previous state.](quantum/test_state.py#L34)**

## Application tests

### Circuit files

- ✅ **[Every rule checked when opening a file is checked when building a circuit, so it cannot be saved.](application/test_circuit_files.py#L68)**
  - ✅ [`(case='unknown gate')`](application/test_circuit_files.py#L68)
  - ✅ [`(case='CNOT on one wire')`](application/test_circuit_files.py#L68)
  - ✅ [`(case='bad initial bits')`](application/test_circuit_files.py#L68)
  - ✅ [`(case='too many qubits')`](application/test_circuit_files.py#L68)
  - ✅ [`(case='undefined base gate')`](application/test_circuit_files.py#L68)
- ✅ **[An exported gate carries each custom gate it needs once, and acts the same on every basis input.](application/test_circuit_files.py#L50)**
- ✅ **[A circuit with nested custom gates reopens in a fresh session with the same columns, gates, settings and amplitudes.](application/test_circuit_files.py#L20)**
  - ✅ [`(settings=RunSettings(seed=5, p=0))`](application/test_circuit_files.py#L20)
  - ✅ [`(settings=None)`](application/test_circuit_files.py#L20)
- ✅ **[The shared Bell circuit opens in the current format and gives 50% for 00 and 11.](application/test_circuit_files.py#L81)**

### Circuit view

- ✅ **[Hover outlines an occupied cell, but a gate dragged onto it outlines nothing, even after a redraw.](application/test_circuit_view.py#L136)**
- ✅ **[CU2 with its control on q3 draws a dot there and a U2 box on q0 and q1, numbered 1 and 2.](application/test_circuit_view.py#L98)**
- ✅ **[CY from q3 to q0 draws a control dot on q3, a Y box on q0, and no symbol on q1 or q2.](application/test_circuit_view.py#L72)**
  - ✅ [`(wire=1, item='QGraphicsEllipseItem')`](application/test_circuit_view.py#L72)
  - ✅ [`(wire=1, item='QGraphicsRectItem')`](application/test_circuit_view.py#L72)
  - ✅ [`(wire=1, item='QGraphicsSimpleTextItem')`](application/test_circuit_view.py#L72)
  - ✅ [`(wire=2, item='QGraphicsEllipseItem')`](application/test_circuit_view.py#L72)
  - ✅ [`(wire=2, item='QGraphicsRectItem')`](application/test_circuit_view.py#L72)
  - ✅ [`(wire=2, item='QGraphicsSimpleTextItem')`](application/test_circuit_view.py#L72)
- ✅ **[A two-wire matrix gate on q3 and q0 numbers those wires in gate order and leaves q1 and q2 unmarked.](application/test_circuit_view.py#L89)**
- ✅ **[A wide gate name stays fully visible inside its box without covering the wire numbers.](application/test_circuit_view.py#L109)**

### Editor

- ✅ **[Placing, removing or clearing gates discards the last run's result.](application/test_editor.py#L51)**
  - ✅ [`(edit='place')`](application/test_editor.py#L51)
  - ✅ [`(edit='remove')`](application/test_editor.py#L51)
  - ✅ [`(edit='clear')`](application/test_editor.py#L51)
- ✅ **[Lowering the qubit count removes gates on missing wires and reselects H if needed.](application/test_editor.py#L68)**
- ✅ **[Opening a gate replaces the circuit. Saving it changes the gate for every use, and a new circuit replaces it.](application/test_editor.py#L104)**
- ✅ **[A custom gate can be deleted only when no placed gate, controlled gate or gate from a circuit uses it.](application/test_editor.py#L81)**
  - ✅ [`(gate='H')`](application/test_editor.py#L81)
  - ✅ [`(gate='CRot')`](application/test_editor.py#L81)
  - ✅ [`(gate='Rot')`](application/test_editor.py#L81)
- ✅ **[An invalid cell leaves a pending CNOT ready for its original target.](application/test_editor.py#L40)**
  - ✅ [`(step=1, wire=2)`](application/test_editor.py#L40)
  - ✅ [`(step=1, wire=-1)`](application/test_editor.py#L40)
  - ✅ [`(step=1, wire=True)`](application/test_editor.py#L40)
  - ✅ [`(step=-1, wire=1)`](application/test_editor.py#L40)
  - ✅ [`(step=0.5, wire=1)`](application/test_editor.py#L40)
- ✅ **[Editing or starting a newer run cancels an iterator even before its first step.](application/test_editor.py#L18)**

### Gate library

- ✅ **[An identical gate is reused. A clash renames the incoming gate, with gates built on it following, or uses the local gate.](application/test_gate_library.py#L124)**
- ✅ **[Gates from circuits with unknown gates, measurements, bad wires, no operations or a cycle are rejected.](application/test_gate_library.py#L101)**
  - ✅ [`(case='unknown gate')`](application/test_gate_library.py#L101)
  - ✅ [`(case='measurement')`](application/test_gate_library.py#L101)
  - ✅ [`(case='too few wires')`](application/test_gate_library.py#L101)
  - ✅ [`(case='wire outside the gate')`](application/test_gate_library.py#L101)
  - ✅ [`(case='repeated wire')`](application/test_gate_library.py#L101)
  - ✅ [`(case='no operations')`](application/test_gate_library.py#L101)
  - ✅ [`(case='uses itself')`](application/test_gate_library.py#L101)
  - ✅ [`(case='cycle')`](application/test_gate_library.py#L101)
  - ✅ [`(case='operation without wires')`](application/test_gate_library.py#L101)
- ✅ **[Matrix cells accept complex numbers, powers, sqrt, exp, pi, e and i, and nothing else.](application/test_gate_library.py#L56)**
  - ✅ [`(text='0.5-0.5i')`](application/test_gate_library.py#L56)
  - ✅ [`(text='-i')`](application/test_gate_library.py#L56)
  - ✅ [`(text='1/sqrt(2)')`](application/test_gate_library.py#L56)
  - ✅ [`(text='exp(i*pi/4)')`](application/test_gate_library.py#L56)
  - ✅ [`(text='e^(i*pi)')`](application/test_gate_library.py#L56)
  - ✅ [`(text='-1^2')`](application/test_gate_library.py#L56)
  - ✅ [`(text='2*3^2')`](application/test_gate_library.py#L56)
  - ✅ [`(text='sqrt(-1)')`](application/test_gate_library.py#L56)
  - ✅ [`(text='cos(pi)')`](application/test_gate_library.py#L56)
  - ✅ [`(text='-i*sin(pi/2)')`](application/test_gate_library.py#L56)
  - ✅ [`(text='')`](application/test_gate_library.py#L56)
  - ✅ [`(text='abc')`](application/test_gate_library.py#L56)
  - ✅ [`(text='1/0')`](application/test_gate_library.py#L56)
  - ✅ [`(text="__import__('os')")`](application/test_gate_library.py#L56)
- ✅ **[Rounded unitaries become exact unitaries; wrong sizes, non-finite, nonunitary and taken names fail.](application/test_gate_library.py#L32)**
  - ✅ [`(entry=0.70710678)`](application/test_gate_library.py#L32)
  - ✅ [`(entry=0.7071)`](application/test_gate_library.py#L32)
  - ✅ [`(case='3 digits')`](application/test_gate_library.py#L32)
  - ✅ [`(case='diag(1, 1.001)')`](application/test_gate_library.py#L32)
  - ✅ [`(case='3x3 matrix')`](application/test_gate_library.py#L32)
  - ✅ [`(case='NaN entry')`](application/test_gate_library.py#L32)
  - ✅ [`(case='infinite entry')`](application/test_gate_library.py#L32)
  - ✅ [`(case='huge entry')`](application/test_gate_library.py#L32)
  - ✅ [`(case='built-in name')`](application/test_gate_library.py#L32)
  - ✅ [`(case='name of another gate')`](application/test_gate_library.py#L32)
- ✅ **[A named two-wire matrix on q3 and q0 matches applying the matrix to those wires directly.](application/test_gate_library.py#L79)**

### Runner

- ✅ **[Leading, internal and trailing empty columns retain their positions on import.](application/test_runner.py#L135)**
  - ✅ [`(columns=[])`](application/test_runner.py#L135)
  - ✅ [`(columns=[[], []])`](application/test_runner.py#L135)
  - ✅ [`(columns=[[], [{'gate': 'H', 'wires': [0]}], [], [{'gate': 'CNOT', 'wires': [0, 1]}], [], []])`](application/test_runner.py#L135)
- ✅ **[Document import and Python construction reject invalid wires at placement validation.](application/test_runner.py#L125)**
  - ✅ [`(wires=(0, 0))`](application/test_runner.py#L125)
  - ✅ [`(wires=(0, 2))`](application/test_runner.py#L125)
  - ✅ [`(wires=(-1, 1))`](application/test_runner.py#L125)
  - ✅ [`(wires=(True, False))`](application/test_runner.py#L125)
  - ✅ [`(wires=(0, 1.0))`](application/test_runner.py#L125)
- ✅ **[The server returns every Bell-state outcome at full precision, as the Python run does.](application/test_runner.py#L79)**
- ✅ **[A request defining a Bell gate from a circuit on q3 and q1 gives the same state as the Python definition.](application/test_runner.py#L90)**
- ✅ **[Invalid circuits, a negative seed and nonzero noise return status 400 with a message.](application/test_runner.py#L105)**
  - ✅ [`(case='unknown gate')`](application/test_runner.py#L105)
  - ✅ [`(case='missing wire')`](application/test_runner.py#L105)
  - ✅ [`(case='wire outside register')`](application/test_runner.py#L105)
  - ✅ [`(case='boolean wire')`](application/test_runner.py#L105)
  - ✅ [`(case='negative seed')`](application/test_runner.py#L105)
  - ✅ [`(case='noise')`](application/test_runner.py#L105)
- ✅ **[The backend, editor session and server import while Qt is blocked.](application/test_runner.py#L42)**
- ✅ **[Gates run by column, not in the order they were placed.](application/test_runner.py#L36)**
- ✅ **[Missing, malformed, ambiguous and oversized lengths get a client error before reading.](application/test_runner.py#L149)**
  - ✅ [`(lengths=[])`](application/test_runner.py#L149)
  - ✅ [`(lengths=['-1'])`](application/test_runner.py#L149)
  - ✅ [`(lengths=['1.5'])`](application/test_runner.py#L149)
  - ✅ [`(lengths=['1', '2'])`](application/test_runner.py#L149)
  - ✅ [`(lengths=['1048577'])`](application/test_runner.py#L149)

### Validation

- ✅ **[Invalid qubit counts and bits.](application/test_validation.py#L46)**
  - ✅ [`(count=0)`](application/test_validation.py#L46)
  - ✅ [`(count=-1)`](application/test_validation.py#L46)
  - ✅ [`(count=2.5)`](application/test_validation.py#L46)
  - ✅ [`(bits='0')`](application/test_validation.py#L46)
  - ✅ [`(bits='000')`](application/test_validation.py#L46)
  - ✅ [`(bits='0x')`](application/test_validation.py#L46)
  - ✅ [`(bits=[0, 2])`](application/test_validation.py#L46)
  - ✅ [`(bits=[0, 0.5])`](application/test_validation.py#L46)
- ✅ **[Invalid gates leave the state intact.](application/test_validation.py#L13)**
  - ✅ [`(gate='missing', wires=(0,))`](application/test_validation.py#L13)
  - ✅ [`(gate='H', wires=())`](application/test_validation.py#L13)
  - ✅ [`(gate='H', wires=(-1,))`](application/test_validation.py#L13)
  - ✅ [`(gate='X', wires=(2,))`](application/test_validation.py#L13)
  - ✅ [`(gate='CNOT', wires=(0,))`](application/test_validation.py#L13)
  - ✅ [`(gate='CNOT', wires=(0, 0))`](application/test_validation.py#L13)
  - ✅ [`(gate=[[1, 0], [0, 1]], wires=(0, 1))`](application/test_validation.py#L13)
  - ✅ [`(gate=[[0.5, 0.5], [0.5, 0.5]], wires=(0,))`](application/test_validation.py#L13)
  - ✅ [`(gate=[[5, 4], [3, 7]], wires=(0,))`](application/test_validation.py#L13)

### Window

- ✅ **[Closing during a run discards unfinished results.](application/test_window.py#L664)**
- ✅ **[A failed run returns to the editor and can be retried.](application/test_window.py#L651)**
- ✅ **[Run shows loading, then the Bell pair can be measured.](application/test_window.py#L629)**
- ✅ **[Typing 25 qubits shows a warning and keeps 2 qubits, so no oversized state is built.](application/test_window.py#L617)**
- ✅ **[An opened circuit shows all 30 of its empty columns, so a gate can be dropped in the last one.](application/test_window.py#L224)**
- ✅ **[A saved circuit reopens after New circuit and runs the same, with its name in the heading. An invalid file leaves it open.](application/test_window.py#L182)**
- ✅ **[Closing asks before losing a custom gate that no saved file holds. Saving a circuit that uses it settles it.](application/test_window.py#L503)**
- ✅ **[A clashing gate in an opened circuit is renamed or replaced by mine. A cancel or a bad gate file changes nothing.](application/test_window.py#L374)**
- ✅ **[Use mine with a local matrix gate keeps the open circuit and edits nothing. Cancel leaves the palette alone.](application/test_window.py#L430)**
- ✅ **[A gate survives overwriting one copy, but losing its last file triggers the close warning.](application/test_window.py#L479)**
- ✅ **[Editing one of two independent gates in a file and saving it rewrites only that gate.](application/test_window.py#L456)**
- ✅ **[A placed custom gate shows its matrix but cannot be deleted until it is removed from the circuit.](application/test_window.py#L570)**
- ✅ **[A six-wire gate shows a note instead of building its 64×64 matrix table.](application/test_window.py#L596)**
- ✅ **[Dragging H and CNOT after right-clicking away a stray X gives the Python Bell state.](application/test_window.py#L100)**
- ✅ **[Dragging CY from q3 to q0 turns 0001 into +i on 1001. From q0 to q3, 0001 is unchanged.](application/test_window.py#L118)**
  - ✅ [`(wires=(3, 0))`](application/test_window.py#L118)
  - ✅ [`(wires=(0, 3))`](application/test_window.py#L118)
- ✅ **[Choosing a new column restarts Toffoli at its first control.](application/test_window.py#L159)**
- ✅ **[A CNOT keeps its control after a duplicate or blocked target.](application/test_window.py#L140)**
- ✅ **[Disposing of a busy window destroys its timer.](application/test_window.py#L716)**
- ✅ **[Rerunning and clearing release previous states.](application/test_window.py#L694)**
- ✅ **[Lowering the qubit count asks before removing gates. Cancel keeps them, and OK removes them.](application/test_window.py#L548)**
- ✅ **[Opening, starting a new circuit or closing asks first. Cancel keeps the circuit, and Don't save goes ahead.](application/test_window.py#L530)**
- ✅ **[Create adds an unsaved gate. Create and save… stays open after a cancel or failed write, then saves the gate with its base.](application/test_window.py#L326)**
- ✅ **[A typed matrix becomes a palette gate that runs like its matrix. A nonunitary one cannot be added.](application/test_window.py#L292)**
- ✅ **[A saved gate from a circuit opens for editing and saves back to its own file, and an older circuit can use mine.](application/test_window.py#L240)**
- ✅ **[The course logo loads at its fixed height below the results.](application/test_window.py#L679)**

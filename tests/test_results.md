# Test results

**✅ Passed** · 61 tests run

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
- ✅ **[Reversed and nonadjacent wires.](quantum/test_gates.py#L165)**
  - ✅ [`(gate='CNOT', wires=(3, 0), input='0001')`](quantum/test_gates.py#L165)
  - ✅ [`(gate='CNOT', wires=(3, 0), input='1000')`](quantum/test_gates.py#L165)
  - ✅ [`(gate='CNOT10', wires=(0, 2), input='0010')`](quantum/test_gates.py#L165)
  - ✅ [`(gate='SWAP', wires=(2, 0), input='0011')`](quantum/test_gates.py#L165)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='1101')`](quantum/test_gates.py#L165)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='1100')`](quantum/test_gates.py#L165)
  - ✅ [`(gate='TOFFOLI', wires=(3, 0, 2), input='0101')`](quantum/test_gates.py#L165)

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

### Circuit view

- ✅ **[CY from q3 to q0 draws a control dot on q3, a Y box on q0, and no symbol on q1 or q2.](application/test_circuit_view.py#L46)**
  - ✅ [`(wire=1, item='QGraphicsEllipseItem')`](application/test_circuit_view.py#L46)
  - ✅ [`(wire=1, item='QGraphicsRectItem')`](application/test_circuit_view.py#L46)
  - ✅ [`(wire=1, item='QGraphicsSimpleTextItem')`](application/test_circuit_view.py#L46)
  - ✅ [`(wire=2, item='QGraphicsEllipseItem')`](application/test_circuit_view.py#L46)
  - ✅ [`(wire=2, item='QGraphicsRectItem')`](application/test_circuit_view.py#L46)
  - ✅ [`(wire=2, item='QGraphicsSimpleTextItem')`](application/test_circuit_view.py#L46)
- ✅ **[A named box on q3 and q0 numbers those wires in gate order and leaves q1 and q2 unmarked.](application/test_circuit_view.py#L63)**

### Editor

- ✅ **[Placing, removing or clearing gates discards the last run's result.](application/test_editor.py#L50)**
  - ✅ [`(edit='place')`](application/test_editor.py#L50)
  - ✅ [`(edit='remove')`](application/test_editor.py#L50)
  - ✅ [`(edit='clear')`](application/test_editor.py#L50)
- ✅ **[Lowering the qubit count removes gates on missing wires and reselects H if needed.](application/test_editor.py#L67)**
- ✅ **[An invalid cell leaves a pending CNOT ready for its original target.](application/test_editor.py#L39)**
  - ✅ [`(step=1, wire=2)`](application/test_editor.py#L39)
  - ✅ [`(step=1, wire=-1)`](application/test_editor.py#L39)
  - ✅ [`(step=1, wire=True)`](application/test_editor.py#L39)
  - ✅ [`(step=-1, wire=1)`](application/test_editor.py#L39)
  - ✅ [`(step=0.5, wire=1)`](application/test_editor.py#L39)
- ✅ **[Editing or starting a newer run cancels an iterator even before its first step.](application/test_editor.py#L17)**

### Runner

- ✅ **[Leading, internal and trailing empty columns retain their positions on import.](application/test_runner.py#L119)**
  - ✅ [`(columns=[])`](application/test_runner.py#L119)
  - ✅ [`(columns=[[], []])`](application/test_runner.py#L119)
  - ✅ [`(columns=[[], [{'gate': 'H', 'wires': [0]}], [], [{'gate': 'CNOT', 'wires': [0, 1]}], [], []])`](application/test_runner.py#L119)
- ✅ **[Document import and Python construction reject invalid wires at placement validation.](application/test_runner.py#L109)**
  - ✅ [`(wires=(0, 0))`](application/test_runner.py#L109)
  - ✅ [`(wires=(0, 2))`](application/test_runner.py#L109)
  - ✅ [`(wires=(-1, 1))`](application/test_runner.py#L109)
  - ✅ [`(wires=(True, False))`](application/test_runner.py#L109)
  - ✅ [`(wires=(0, 1.0))`](application/test_runner.py#L109)
- ✅ **[The server returns every Bell-state outcome at full precision, as the Python run does.](application/test_runner.py#L79)**
- ✅ **[Invalid circuits and nonzero noise return status 400 with a message.](application/test_runner.py#L90)**
  - ✅ [`(case='unknown gate')`](application/test_runner.py#L90)
  - ✅ [`(case='missing wire')`](application/test_runner.py#L90)
  - ✅ [`(case='wire outside register')`](application/test_runner.py#L90)
  - ✅ [`(case='boolean wire')`](application/test_runner.py#L90)
  - ✅ [`(case='noise')`](application/test_runner.py#L90)
- ✅ **[The backend, editor session and server import while Qt is blocked.](application/test_runner.py#L42)**
- ✅ **[Gates run by column, not in the order they were placed.](application/test_runner.py#L36)**
- ✅ **[Missing, malformed, ambiguous and oversized lengths get a client error before reading.](application/test_runner.py#L133)**
  - ✅ [`(lengths=[])`](application/test_runner.py#L133)
  - ✅ [`(lengths=['-1'])`](application/test_runner.py#L133)
  - ✅ [`(lengths=['1.5'])`](application/test_runner.py#L133)
  - ✅ [`(lengths=['1', '2'])`](application/test_runner.py#L133)
  - ✅ [`(lengths=['1048577'])`](application/test_runner.py#L133)

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

- ✅ **[Closing during a run discards unfinished results.](application/test_window.py#L183)**
- ✅ **[A failed run returns to the editor and can be retried.](application/test_window.py#L170)**
- ✅ **[Run shows loading, then the Bell pair can be measured.](application/test_window.py#L148)**
- ✅ **[Dragging H and CNOT after right-clicking away a stray X gives the Python Bell state.](application/test_window.py#L66)**
- ✅ **[Dragging CY from q3 to q0 turns 0001 into +i on 1001. From q0 to q3, 0001 is unchanged.](application/test_window.py#L84)**
  - ✅ [`(wires=(3, 0))`](application/test_window.py#L84)
  - ✅ [`(wires=(0, 3))`](application/test_window.py#L84)
- ✅ **[Choosing a new column restarts Toffoli at its first control.](application/test_window.py#L125)**
- ✅ **[A CNOT keeps its control after a duplicate or blocked target.](application/test_window.py#L106)**
- ✅ **[Disposing of a busy window destroys its timer.](application/test_window.py#L235)**
- ✅ **[Rerunning and clearing release previous states.](application/test_window.py#L213)**
- ✅ **[The course logo loads at its fixed height below the results.](application/test_window.py#L198)**

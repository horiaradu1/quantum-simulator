# Assignment

## AI use

You may use AI to develop the simulator if you understand the code. The team must create the presentation without AI (p. 4).

## Simulator conventions

The register starts in `|00…0⟩`. Basis labels put `q0` on the left. Gate calls list wires in matrix order, with CNOT and CH taking the control first and Toffoli taking both controls before the target.

The simulator returns fixed-width basis labels from `sample()` and `measure()`. Sampling preserves the state. Measurement collapses the full register. `outcomes()` supplies basis labels, complex amplitudes, and probabilities for display.

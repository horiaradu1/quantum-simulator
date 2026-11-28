"""Describe how an editor lists, places, draws and explains each built-in gate.

Gate IDs match the names that gate_matrix accepts. GATE_CATALOG lists them in palette order.
"""

from dataclasses import dataclass
from enum import Enum, auto


class WireMark(Enum):
    """A circuit symbol that a gate draws on one of its wires."""

    CONTROL = auto()
    NOT = auto()
    SWAP = auto()


@dataclass(frozen=True)
class GateSpec:
    """A gate's palette label, the wire roles an editor asks for, and its circuit symbol.

    Each symbol is a mark or the text of a box drawn on that wire, in the gate's wire order.
    A gate without symbols is drawn as a control dot on each of its first control_count wires
    and one box over the other wires, labelled box_label or, without one, the gate's label.
    """

    label: str
    wire_roles: tuple[str, ...]
    symbols: tuple[WireMark | str, ...] | None = None
    description: str = ""
    control_count: int = 0
    box_label: str | None = None

    @property
    def wire_count(self) -> int:
        return len(self.wire_roles)


_TARGET = ("target",)
_CONTROL_AND_TARGET = ("control", "target")

GATE_CATALOG: dict[str, GateSpec] = {
    "H": GateSpec("H", _TARGET, description="Hadamard. Maps |0⟩ to |+⟩ and |1⟩ to |−⟩."),
    "X": GateSpec("X", _TARGET, description="Pauli-X, or NOT. Swaps |0⟩ and |1⟩."),
    "Y": GateSpec("Y", _TARGET, description="Pauli-Y. Maps |0⟩ to i|1⟩ and |1⟩ to −i|0⟩."),
    "Z": GateSpec("Z", _TARGET, description="Pauli-Z. Multiplies |1⟩ by −1."),
    "S": GateSpec("S", _TARGET, description="Phase gate. Multiplies |1⟩ by i."),
    "T": GateSpec("T", _TARGET, description="T gate. Multiplies |1⟩ by e^(iπ/4)."),
    "CNOT": GateSpec(
        "CNOT", _CONTROL_AND_TARGET, (WireMark.CONTROL, WireMark.NOT),
        description="Controlled-X. Flips the target when the control is 1.",
    ),
    "CH": GateSpec(
        "CH", _CONTROL_AND_TARGET, (WireMark.CONTROL, "H"),
        description="Controlled-H. Applies H to the target when the control is 1.",
    ),
    "CY": GateSpec(
        "CY", _CONTROL_AND_TARGET, (WireMark.CONTROL, "Y"),
        description="Controlled-Y. Applies Y to the target when the control is 1.",
    ),
    "CZ": GateSpec(
        "CZ", _CONTROL_AND_TARGET, (WireMark.CONTROL, "Z"),
        description="Controlled-Z. Multiplies |11⟩ by −1.",
    ),
    "CS": GateSpec(
        "CS", _CONTROL_AND_TARGET, (WireMark.CONTROL, "S"),
        description="Controlled-S. Multiplies |11⟩ by i.",
    ),
    "CT": GateSpec(
        "CT", _CONTROL_AND_TARGET, (WireMark.CONTROL, "T"),
        description="Controlled-T. Multiplies |11⟩ by e^(iπ/4).",
    ),
    "SWAP": GateSpec(
        "SWAP", ("first wire", "second wire"), (WireMark.SWAP, WireMark.SWAP),
        description="Exchanges the states of its two wires.",
    ),
    "TOFFOLI": GateSpec(
        "Toffoli",
        ("first control", "second control", "target"),
        (WireMark.CONTROL, WireMark.CONTROL, WireMark.NOT),
        description="Controlled-controlled-X. Flips the target when both controls are 1.",
    ),
}

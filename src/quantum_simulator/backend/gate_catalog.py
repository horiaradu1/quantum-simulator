"""Describe how an editor lists, places and draws each built-in gate.

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
    A gate without symbols is drawn as a box labelled with its name.
    """

    label: str
    wire_roles: tuple[str, ...]
    symbols: tuple[WireMark | str, ...] | None = None

    @property
    def wire_count(self) -> int:
        return len(self.wire_roles)


_TARGET = ("target",)
_CONTROL_AND_TARGET = ("control", "target")

GATE_CATALOG: dict[str, GateSpec] = {
    "H": GateSpec("H", _TARGET),
    "X": GateSpec("X", _TARGET),
    "Y": GateSpec("Y", _TARGET),
    "Z": GateSpec("Z", _TARGET),
    "S": GateSpec("S", _TARGET),
    "T": GateSpec("T", _TARGET),
    "CNOT": GateSpec("CNOT", _CONTROL_AND_TARGET, (WireMark.CONTROL, WireMark.NOT)),
    "CH": GateSpec("CH", _CONTROL_AND_TARGET, (WireMark.CONTROL, "H")),
    "CY": GateSpec("CY", _CONTROL_AND_TARGET, (WireMark.CONTROL, "Y")),
    "CZ": GateSpec("CZ", _CONTROL_AND_TARGET, (WireMark.CONTROL, "Z")),
    "CS": GateSpec("CS", _CONTROL_AND_TARGET, (WireMark.CONTROL, "S")),
    "CT": GateSpec("CT", _CONTROL_AND_TARGET, (WireMark.CONTROL, "T")),
    "SWAP": GateSpec("SWAP", ("first wire", "second wire"), (WireMark.SWAP, WireMark.SWAP)),
    "TOFFOLI": GateSpec(
        "Toffoli",
        ("first control", "second control", "target"),
        (WireMark.CONTROL, WireMark.CONTROL, WireMark.NOT),
    ),
}

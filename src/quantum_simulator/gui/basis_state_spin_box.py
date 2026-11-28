"""Handle typing and stepping through the initial register's binary values."""

from PySide6.QtGui import QValidator

from .arrow_spin_box import ArrowSpinBox


class BasisStateSpinBox(ArrowSpinBox):
    """Display exactly one bit per qubit, including leading zeros."""

    def __init__(self):
        self._qubit_count = 1
        super().__init__()
        self.setDisplayIntegerBase(2)
        self.set_qubit_count(1)

    def set_qubit_count(self, count: int) -> None:
        bits = self.text()
        if any(bit not in "01" for bit in bits):
            bits = self.textFromValue(self.value())
        resized = bits[:count].ljust(count, "0")
        self._qubit_count = count
        self.setRange(0, 2**count - 1)
        value = int(resized, 2)
        self.setValue(value)
        self.lineEdit().setText(self.textFromValue(value))
        self.lineEdit().setPlaceholderText(f"{count}-bit state")

    def textFromValue(self, value: int) -> str:
        return f"{value:0{self._qubit_count}b}"

    def validate(self, text: str, position: int) -> tuple[QValidator.State, str, int]:
        if len(text) > self._qubit_count or any(bit not in "01" for bit in text):
            state = QValidator.State.Invalid
        elif len(text) < self._qubit_count:
            state = QValidator.State.Intermediate
        else:
            state = QValidator.State.Acceptable
        return state, text, position

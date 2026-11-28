"""Evaluate what users type into a matrix cell, such as 0.5-0.5i, 1/sqrt(2), exp(i*pi/4) or cos(pi/8).

format_complex writes a value back as short text for display.
"""

import ast
import cmath
import math
import operator
import re

_MAX_LENGTH = 200
_CONSTANTS = {"i": 1j, "j": 1j, "pi": math.pi, "e": math.e}
_FUNCTIONS = {"sqrt": cmath.sqrt, "exp": cmath.exp, "cos": cmath.cos, "sin": cmath.sin}
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_IMAGINARY_NUMBER = re.compile(r"((?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)[ij]\b")
_HELP = (
    "Use numbers, i, pi, e, + - * / ^, brackets, sqrt(), exp(), cos() and sin(), "
    "for example 1/sqrt(2) or exp(i*pi/4)."
)


def parse_complex(text: str) -> complex:
    """Evaluate one matrix cell. Raise ValueError if the text is not a supported expression."""
    text = text.strip()
    if not text:
        raise ValueError("The cell is empty.")
    if len(text) > _MAX_LENGTH:
        raise ValueError(f"The cell is longer than {_MAX_LENGTH} characters.")

    source = _IMAGINARY_NUMBER.sub(r"(\1*i)", text)
    source = source.replace("^", "**")
    try:
        tree = ast.parse(source, mode="eval")
        return complex(_evaluate(tree.body))
    except SyntaxError:
        raise ValueError(f"Cannot read {text!r}. {_HELP}") from None
    except (ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"Cannot evaluate {text!r}: {error}.") from None


def format_complex(value: complex) -> str:
    """Write a value with up to 4 decimals and no trailing zeros, such as 0.7071+0.7071i or -i."""

    def number(part: float) -> str:
        return f"{round(part, 4) + 0.0:.4f}".rstrip("0").rstrip(".")

    def imaginary_part(coefficient: str) -> str:
        return "i" if coefficient == "1" else f"{coefficient}i"

    real, imaginary = number(value.real), number(value.imag)
    if imaginary == "0":
        return real
    if real == "0":
        return "-i" if imaginary == "-1" else imaginary_part(imaginary)
    sign = "+" if value.imag > 0 else "-"
    return f"{real}{sign}{imaginary_part(number(abs(value.imag)))}"


def _evaluate(node: ast.expr) -> complex:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float, complex):
        return complex(node.value)
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return complex(_CONSTANTS[node.id])
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        return 0 - value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        apply_operator = _OPERATORS[type(node.op)]
        return apply_operator(_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
        if len(node.args) != 1 or node.keywords:
            raise ValueError(f"{node.func.id}() takes exactly one value.")
        return _FUNCTIONS[node.func.id](_evaluate(node.args[0]))
    raise ValueError(f"Unsupported part of the expression. {_HELP}")

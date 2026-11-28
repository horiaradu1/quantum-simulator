"""Save and open gate files, each holding a gate and every custom gate it is built from."""

from collections.abc import Iterable, Sequence
from importlib.resources.abc import Traversable
from pathlib import Path

from .circuit import FORMAT_VERSION
from .gate_library import GateDefinition, GateLibrary, definition_from_dict
from .json_file import read_json, write_json


def gate_file_document(definitions: Sequence[GateDefinition]) -> dict:
    """Write the gate file document for these definitions."""
    return {
        "kind": "gate_file",
        "version": FORMAT_VERSION,
        "definitions": [definition.to_dict() for definition in definitions],
    }


def definitions_from_document(document: object) -> tuple[GateDefinition, ...]:
    """Read a gate file document. Raise ValueError if it is invalid or uses a gate it does not define."""
    if not isinstance(document, dict) or document.get("kind") != "gate_file":
        raise ValueError('Expected a gate file with "kind": "gate_file".')
    if type(document.get("version")) is not int or document["version"] != FORMAT_VERSION:
        raise ValueError(f"Unsupported gate file format version {document.get('version')!r}.")
    entries = document.get("definitions")
    if not isinstance(entries, list):
        raise ValueError('"definitions" must be a list of gate definitions.')

    definitions = tuple(definition_from_dict(entry) for entry in entries)
    # Building a library checks every reference, wire count and cycle.
    GateLibrary(definitions)
    return definitions


def export_gates(path: Path, library: GateLibrary, gate_ids: Iterable[str]) -> tuple[GateDefinition, ...]:
    """Write a gate file with these gates and every custom gate they use, once each. Return what was written.

    Raise OSError if the write fails, leaving any earlier file unchanged.
    """
    definitions = library.definitions_for(gate_ids)
    save_gates(path, definitions)
    return definitions


def save_gates(path: Path, definitions: Sequence[GateDefinition]) -> None:
    """Write a gate file. Raise OSError if it fails, leaving any earlier file unchanged."""
    write_json(path, gate_file_document(definitions))


def load_gates(path: Traversable) -> tuple[GateDefinition, ...]:
    """Read a gate file. Raise ValueError if it cannot be used."""
    return definitions_from_document(read_json(path))

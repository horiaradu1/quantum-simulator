"""Save and open circuit files, and list the shared circuits that ship with the simulator."""

import re
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from .circuit import Circuit
from .json_file import DATA_DIRECTORY, read_json, write_json
from .runner import RunSettings

SAVED_CIRCUITS = DATA_DIRECTORY / "circuits"
_SHARED_CIRCUITS = files("quantum_simulator") / "resources" / "circuits"
_NAME_PATTERN = re.compile(r"[\w\- ]+")


def saved_circuit_path(name: str, directory: Path = SAVED_CIRCUITS) -> Path:
    """Return the file for a saved circuit name. Raise ValueError if the name is not usable."""
    name = name.strip()
    if not _NAME_PATTERN.fullmatch(name):
        raise ValueError("Use only letters, digits, spaces, hyphens and underscores in the name.")
    return directory / f"{name}.json"


def save_circuit(path: Path, circuit: Circuit, settings: RunSettings | None = None) -> None:
    """Write a circuit file with every custom gate it uses, and any run settings apart from the columns."""
    document = circuit.to_dict()
    if settings is not None:
        document["settings"] = settings.to_dict()
    write_json(path, document)


def load_circuit(path: Traversable) -> tuple[Circuit, RunSettings | None]:
    """Read a circuit file and its optional settings. Raise ValueError if it cannot be used."""
    document = read_json(path)
    circuit = Circuit.from_dict(document)
    settings_document = document.get("settings")
    settings = None if settings_document is None else RunSettings.from_dict(settings_document)
    return circuit, settings


def shared_circuits() -> dict[str, Traversable]:
    """Map each shared circuit's name to its file, in name order."""
    circuits = {}
    for entry in sorted(_SHARED_CIRCUITS.iterdir(), key=lambda entry: entry.name):
        if entry.name.endswith(".json"):
            circuits[entry.name.removesuffix(".json")] = entry
    return circuits

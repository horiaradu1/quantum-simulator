"""Save and open circuit files, and list the shared circuits that ship with the simulator."""

import json
import re
import tempfile
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from .circuit import Circuit
from .runner import RunSettings

SAVED_CIRCUITS = Path("data") / "circuits"
_SHARED_CIRCUITS = files("quantum_simulator") / "resources" / "circuits"
_NAME_PATTERN = re.compile(r"[\w\- ]+")


def saved_circuit_path(name: str, directory: Path = SAVED_CIRCUITS) -> Path:
    """Return the file for a saved circuit name. Raise ValueError if the name is not usable."""
    name = name.strip()
    if not _NAME_PATTERN.fullmatch(name):
        raise ValueError("Use only letters, digits, spaces, hyphens and underscores in the name.")
    return directory / f"{name}.json"


def save_circuit(path: Path, circuit: Circuit, settings: RunSettings | None = None) -> None:
    """Write a circuit file, with any run settings stored apart from the columns."""
    document = circuit.to_dict()
    if settings is not None:
        document["settings"] = settings.to_dict()

    text = json.dumps(document, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Temp file to prevent corruption of saved files
    temporary_file = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f"{path.name}.", suffix=".tmp", delete=False
    )
    temporary_path = Path(temporary_file.name)
    try:
        with temporary_file:
            temporary_file.write(text)
        temporary_path.replace(path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def load_circuit(path: Traversable) -> tuple[Circuit, RunSettings | None]:
    """Read a circuit file and its optional settings. Raise ValueError if it cannot be used."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Could not read {path.name}: {error.strerror or error}.") from error
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name} is not valid JSON: {error.msg} on line {error.lineno}.") from error

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

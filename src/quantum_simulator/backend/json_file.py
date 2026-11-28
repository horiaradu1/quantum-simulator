"""Read and write the simulator's JSON files, keeping the previous file if a write fails."""

import json
import tempfile
from importlib.resources.abc import Traversable
from pathlib import Path

# Local saves live under the directory the app runs from.
DATA_DIRECTORY = Path("data")


def read_json(path: Traversable) -> object:
    """Read a JSON file. Raise ValueError with a readable message if it cannot be read."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Could not read {path.name}: {error.strerror or error}.") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name} is not valid JSON: {error.msg} on line {error.lineno}.") from error


def write_json(path: Path, document: object) -> None:
    """Write a JSON file. Raise OSError if it fails, leaving any earlier file unchanged."""
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

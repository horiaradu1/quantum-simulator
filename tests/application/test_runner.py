"""Run circuits through the Python API and the HTTP server, without Qt."""

import json
import subprocess
import sys
import threading
import unittest
from email.message import Message
from math import sqrt
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from quantum_simulator import Circuit, PlacedGate, run
from quantum_simulator.server import MAX_REQUEST_BYTES, SimulationHandler, create_server

BELL_DOCUMENT = {
    "kind": "circuit",
    "version": 1,
    "qubits": 2,
    "initial_bits": "00",
    "columns": [
        [{"gate": "H", "wires": [0]}],
        [{"gate": "CNOT", "wires": [0, 1]}],
    ],
    "settings": {"seed": 7, "p": 0},
}


class TestPythonRun(unittest.TestCase):
    """Run circuits with the Python call that the desktop app also uses."""

    def test_columns_run_in_order(self):
        """Gates run by column, not in the order they were placed."""
        # H then X keeps |+>. X then H would give |->.
        circuit = Circuit(1, "0", (PlacedGate(1, "X", (0,)), PlacedGate(0, "H", (0,))))
        assert_allclose(run(circuit).amplitudes, np.array([1, 1]) / sqrt(2))

    def test_backend_and_server_import_without_qt(self):
        """The backend, editor session and server import while Qt is blocked."""
        script = (
            "import sys; sys.modules['PySide6'] = None; "
            "import quantum_simulator.backend.editor, quantum_simulator.server"
        )
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class TestHttpServer(unittest.TestCase):
    """Send circuit documents to POST /simulate on a local server."""

    def setUp(self):
        quiet_logging = patch.object(SimulationHandler, "log_message")
        quiet_logging.start()
        self.addCleanup(quiet_logging.stop)

        server = create_server(port=0)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        host, port = server.server_address
        self.url = f"http://{host}:{port}/simulate"

    def post(self, document):
        body = json.dumps(document).encode("utf-8")
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_bell_state_matches_python(self):
        """The server returns every Bell-state outcome at full precision, as the Python run does."""
        status, body = self.post(BELL_DOCUMENT)
        self.assertEqual(status, 200)

        outcomes = body["outcomes"]
        self.assertEqual([outcome["basis"] for outcome in outcomes], ["00", "01", "10", "11"])
        amplitudes = [complex(*outcome["amplitude"]) for outcome in outcomes]
        assert_array_equal(amplitudes, run(Circuit.from_dict(BELL_DOCUMENT)).amplitudes)
        assert_allclose([outcome["probability"] for outcome in outcomes], [0.5, 0, 0, 0.5])

    def test_invalid_requests_return_an_error(self):
        """Invalid circuits and nonzero noise return status 400 with a message."""
        cases = {
            "unknown gate": {"columns": [[{"gate": "CNOT10", "wires": [0, 1]}]]},
            "missing wire": {"columns": [[{"gate": "CNOT", "wires": [0]}]]},
            "wire outside register": {"columns": [[{"gate": "H", "wires": [2]}]]},
            "boolean wire": {"columns": [[{"gate": "X", "wires": [True]}]]},
            "noise": {"settings": {"p": 0.1}},
        }
        for case, changes in cases.items():
            with self.subTest(case=case):
                status, body = self.post(BELL_DOCUMENT | changes)
                self.assertEqual(status, 400)
                self.assertIn("error", body)


class TestCircuitModel(unittest.TestCase):
    """Check the circuit data accepted before simulation."""

    def test_invalid_wires_are_rejected_before_running(self):
        """Document import and Python construction reject invalid wires at placement validation."""
        for wires in ((0, 0), (0, 2), (-1, 1), (True, False), (0, 1.0)):
            with self.subTest(wires=wires):
                document = BELL_DOCUMENT | {"columns": [[{"gate": "CNOT", "wires": list(wires)}]]}
                with self.assertRaisesRegex(ValueError, r"columns\[0\]"):
                    Circuit.from_dict(document)
                with self.assertRaisesRegex(ValueError, r"columns\[0\]"):
                    Circuit(2, "00", (PlacedGate(0, "CNOT", wires),))

    def test_column_count_preserves_empty_columns(self):
        """Leading, internal and trailing empty columns retain their positions on import."""
        h, cnot = BELL_DOCUMENT["columns"]
        cases = (([], []), ([[], []], []), ([[], h, [], cnot, [], []], [1, 3]))
        for columns, occupied_steps in cases:
            with self.subTest(columns=columns):
                circuit = Circuit.from_dict(BELL_DOCUMENT | {"columns": columns})
                self.assertEqual(circuit.column_count, len(columns))
                self.assertEqual([gate.step for gate in circuit.gates], occupied_steps)


class TestRequestLength(unittest.TestCase):
    """Check framing errors before the handler touches the request stream."""

    def test_bad_lengths_are_rejected_before_read(self):
        """Missing, malformed, ambiguous and oversized lengths get a client error before reading."""
        cases = (
            ([], 411),
            (["-1"], 400),
            (["1.5"], 400),
            (["1", "2"], 400),
            ([str(MAX_REQUEST_BYTES + 1)], 413),
        )
        for lengths, status in cases:
            with self.subTest(lengths=lengths):
                handler = Mock()
                handler.path = "/simulate"
                handler.headers = Message()
                for length in lengths:
                    handler.headers["Content-Length"] = length
                SimulationHandler.do_POST(handler)
                handler.rfile.read.assert_not_called()
                actual_status, payload = handler._send_json.call_args.args
                self.assertEqual(actual_status, status)
                self.assertIn("error", payload)

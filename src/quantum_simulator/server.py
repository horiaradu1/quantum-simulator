"""Serve circuit simulations over HTTP.

Start it with `python -m quantum_simulator.server`, then POST a circuit document to /simulate.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .backend import Circuit, RunSettings, run, state_to_dict

MAX_REQUEST_BYTES = 1024 * 1024


class SimulationHandler(BaseHTTPRequestHandler):
    """Answer POST /simulate with the final state of the circuit in the request body."""

    def do_POST(self) -> None:
        if self.path != "/simulate":
            self._send_json(404, {"error": "Use POST /simulate."})
            return

        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get("Transfer-Encoding") is not None:
            self._send_json(400, {"error": "Send a fixed-length JSON body."})
            return
        if not lengths:
            self._send_json(411, {"error": "Content-Length is required."})
            return
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
            self._send_json(400, {"error": "Content-Length must be a single nonnegative integer."})
            return

        try:
            length = int(lengths[0])
            if length > MAX_REQUEST_BYTES:
                self._send_json(413, {"error": f"The request body exceeds {MAX_REQUEST_BYTES} bytes."})
                return
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError("The request body is shorter than Content-Length.")
            document = json.loads(body)
            circuit = Circuit.from_dict(document)
            settings = RunSettings.from_dict(document.get("settings"))
            state = run(circuit, settings)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        self._send_json(200, state_to_dict(state))

    def do_OPTIONS(self) -> None:
        # Browsers send this preflight request before a cross-origin POST with a JSON body.
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), SimulationHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve circuit simulations over HTTP.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()

    server = create_server(arguments.host, arguments.port)
    print(f"Serving POST http://{arguments.host}:{arguments.port}/simulate. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

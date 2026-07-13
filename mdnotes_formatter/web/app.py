"""Local HTTP server that exposes backend endpoints for the web frontend."""

from __future__ import annotations

import json
import mimetypes
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..backend import (
    FormatFileRequest,
    ListMarkdownFilesRequest,
    MarkdownFormatterBackend,
    PreviewFileRequest,
)

_STATIC_DIR = Path(__file__).parent / "static"


class _WebHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving static UI and backend-backed JSON APIs."""

    backend = MarkdownFormatterBackend()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._serve_static("index.html", content_type="text/html; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._serve_static("styles.css", content_type="text/css; charset=utf-8")
            return
        if self.path == "/app.js":
            self._serve_static("app.js", content_type="application/javascript; charset=utf-8")
            return

        if self.path == "/api/health":
            self._write_json(HTTPStatus.OK, self.backend.endpoint_health())
            return

        if self.path == "/api/endpoints":
            payload = [asdict(endpoint) for endpoint in self.backend.endpoint_list_endpoints()]
            self._write_json(HTTPStatus.OK, payload)
            return

        if self.path.startswith("/api/files"):
            self._handle_files_list()
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/preview":
            self._handle_preview()
            return
        if self.path == "/api/format":
            self._handle_format()
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def _handle_files_list(self) -> None:
        """Handle markdown file listing endpoint."""
        try:
            root = self._extract_query_param("root")
            response = self.backend.endpoint_list_markdown_files(
                ListMarkdownFilesRequest(root=root),
            )
            self._write_json(HTTPStatus.OK, asdict(response))
        except Exception as exc:  # pragma: no cover - exercised in integration
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def _handle_preview(self) -> None:
        """Handle non-mutating preview endpoint."""
        try:
            payload = self._read_json_body()
            response = self.backend.endpoint_preview_file(
                PreviewFileRequest(
                    path=payload["path"],
                    selected_advanced_aliases=payload.get("selected_advanced_aliases"),
                ),
            )
            self._write_json(HTTPStatus.OK, asdict(response))
        except Exception as exc:  # pragma: no cover - exercised in integration
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def _handle_format(self) -> None:
        """Handle mutating format endpoint."""
        try:
            payload = self._read_json_body()
            response = self.backend.endpoint_format_file(
                FormatFileRequest(
                    path=payload["path"],
                    selected_advanced_aliases=payload.get("selected_advanced_aliases"),
                ),
            )
            self._write_json(HTTPStatus.OK, asdict(response))
        except Exception as exc:  # pragma: no cover - exercised in integration
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def _serve_static(self, name: str, content_type: str | None = None) -> None:
        """Serve one static file from package assets."""
        file_path = (_STATIC_DIR / name).resolve()
        if not file_path.exists() or not file_path.is_file():
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Static file not found"})
            return

        data = file_path.read_bytes()
        guessed_type = content_type or (mimetypes.guess_type(str(file_path))[0] or "text/plain")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", guessed_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> dict:
        """Read and decode request JSON body."""
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        return json.loads(body.decode("utf-8"))

    def _extract_query_param(self, key: str) -> str | None:
        """Extract one query parameter value from URL path."""
        query = parse_qs(urlparse(self.path).query)
        values = query.get(key)
        if not values:
            return None
        return values[0] or None

    def _write_json(self, status: HTTPStatus, payload: dict | list) -> None:
        """Serialize payload as JSON response."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_web_ui(host: str = "127.0.0.1", port: int = 8765, root: str | None = None) -> None:
    """Start the local web UI server.

    Args:
        host: Bind host for the HTTP server.
        port: Bind port for the HTTP server.
        root: Optional backend root directory for file operations.
    """
    _WebHandler.backend = MarkdownFormatterBackend(root=root)
    server = ThreadingHTTPServer((host, port), _WebHandler)
    url = f"http://{host}:{port}"
    print(f"Web UI running at {url}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web UI server...")
    finally:
        server.server_close()

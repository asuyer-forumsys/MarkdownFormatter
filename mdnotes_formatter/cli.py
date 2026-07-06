"""CLI frontend for markdown formatter backend services.

Architecture note:
- This module is the *frontend* layer.
- It orchestrates argument parsing and presentation only.
- Business logic is delegated to backend endpoints.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .backend import FormatFileRequest, MarkdownFormatterBackend
from .web.app import serve_web_ui


def build_parser() -> argparse.ArgumentParser:
    """Create parser for frontend CLI commands."""
    parser = argparse.ArgumentParser(
        description="Markdown formatter CLI frontend backed by endpoint calls.",
    )

    subparsers = parser.add_subparsers(dest="command")

    format_parser = subparsers.add_parser(
        "format",
        help="Format one markdown file via backend endpoint.",
    )
    format_parser.add_argument("path", help="Path to markdown file")

    subparsers.add_parser(
        "endpoints",
        help="List available backend endpoints and contracts.",
    )

    subparsers.add_parser(
        "health",
        help="Check backend health endpoint.",
    )

    web_parser = subparsers.add_parser(
        "web",
        help="Start local web UI frontend.",
    )
    web_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    web_parser.add_argument("--port", default=8765, type=int, help="Bind port (default: 8765)")
    web_parser.add_argument(
        "--root",
        default=None,
        help="Optional filesystem root for backend file explorer (default: current directory)",
    )

    return parser


def _print_endpoints(backend: MarkdownFormatterBackend) -> None:
    """Print backend endpoint catalog as JSON for frontend introspection."""
    payload = [endpoint.__dict__ for endpoint in backend.endpoint_list_endpoints()]
    print(json.dumps(payload, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    """Run CLI frontend and invoke backend endpoints.

    Args:
        argv: Optional argument vector. Useful for tests.

    Returns:
        Process exit code.
    """
    parser = build_parser()

    normalized_argv = list(argv) if argv is not None else None
    known_commands = {"format", "endpoints", "health", "web"}

    # Legacy compatibility shim:
    # if first token is not a known command, reinterpret invocation as
    # `format <path>`.
    if normalized_argv and normalized_argv[0] not in known_commands:
        normalized_argv = ["format", *normalized_argv]

    args = parser.parse_args(normalized_argv)

    if args.command == "web":
        serve_web_ui(host=args.host, port=args.port, root=args.root)
        return 0

    backend = MarkdownFormatterBackend()

    if args.command == "endpoints":
        _print_endpoints(backend)
        return 0

    if args.command == "health":
        print(json.dumps(backend.endpoint_health()))
        return 0

    if args.command == "format":
        response = backend.endpoint_format_file(FormatFileRequest(path=args.path))
        print(response.updated_path)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

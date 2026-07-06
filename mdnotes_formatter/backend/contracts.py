"""Typed request/response contracts for backend endpoints.

These dataclasses act as a stable API boundary between frontend layers and the
backend implementation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatFileRequest:
    """Input payload for the format-file backend endpoint.

    Attributes:
        path: Path string to an existing `.md` file that should be reformatted.
    """

    path: str


@dataclass(frozen=True)
class FormatFileResponse:
    """Output payload from the format-file backend endpoint.

    Attributes:
        original_path: Original file path received by the endpoint.
        updated_path: Final path where formatted content now resides.
        backup_path: `.bak` path containing the pre-format file content.
        renamed: True when filename normalization renamed the source file.
    """

    original_path: str
    updated_path: str
    backup_path: str
    renamed: bool


@dataclass(frozen=True)
class EndpointInfo:
    """Describes one backend endpoint.

    Attributes:
        name: Stable endpoint identifier.
        method: Logical invocation style (always `local-call` for now).
        summary: One-line human-readable endpoint purpose.
        request_type: Name of the request contract type.
        response_type: Name of the response contract type.
    """

    name: str
    method: str
    summary: str
    request_type: str
    response_type: str

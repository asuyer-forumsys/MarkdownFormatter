"""Backend endpoint implementations.

Design goal:
- Keep formatting logic in backend endpoints that are callable by any frontend.
- Keep transport details out of this module (today local calls, tomorrow GUI,
  web API, IPC, etc.).
"""

from __future__ import annotations

from pathlib import Path

from .contracts import EndpointInfo, FormatFileRequest, FormatFileResponse
from ..formatter import format_markdown_file


class MarkdownFormatterBackend:
    """UI-agnostic backend endpoint surface for markdown formatting.

    Endpoint naming convention follows an `endpoint_*` prefix so future routing
    adapters (HTTP, RPC, desktop bridge) can map and expose endpoints easily.
    """

    def endpoint_health(self) -> dict[str, str]:
        """Health endpoint for frontend readiness checks.

        Returns:
            A simple status dictionary. This is intentionally tiny and stable.
        """
        return {"status": "ok", "service": "mdnotes-formatter-backend"}

    def endpoint_list_endpoints(self) -> list[EndpointInfo]:
        """Return machine-readable metadata for available backend endpoints.

        Returns:
            A list of endpoint descriptors including request/response contracts.
        """
        return [
            EndpointInfo(
                name="health",
                method="local-call",
                summary="Health check endpoint for frontend connectivity.",
                request_type="None",
                response_type="dict[str, str]",
            ),
            EndpointInfo(
                name="format_file",
                method="local-call",
                summary="Format one markdown file, create backup, and rename if needed.",
                request_type="FormatFileRequest",
                response_type="FormatFileResponse",
            ),
        ]

    def endpoint_format_file(self, request: FormatFileRequest) -> FormatFileResponse:
        """Format and normalize one markdown note file.

        Endpoint contract:
            - Input: `FormatFileRequest`
            - Output: `FormatFileResponse`

        Side effects:
            - Writes formatted markdown content.
            - Creates `<original>.bak` backup.
            - Renames file when normalized filename differs.

        Raises:
            ValueError: If file extension is not `.md`.
            FileNotFoundError: If the requested file path does not exist.
        """
        original_path = Path(request.path)
        updated_path = format_markdown_file(original_path)

        return FormatFileResponse(
            original_path=str(original_path),
            updated_path=str(updated_path),
            backup_path=str(original_path.with_name(original_path.name + ".bak")),
            renamed=updated_path != original_path,
        )

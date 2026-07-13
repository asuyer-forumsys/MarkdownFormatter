"""Backend package for markdown formatter business logic.

This backend layer is intentionally UI-agnostic. Any frontend (CLI today,
web UI/desktop later) should call these backend endpoints instead of touching
formatting internals directly.
"""

from .contracts import (
    AliasSuggestion,
    EndpointInfo,
    FormatFileRequest,
    FormatFileResponse,
    ListMarkdownFilesRequest,
    ListMarkdownFilesResponse,
    PreviewFileRequest,
    PreviewFileResponse,
)
from .endpoints import MarkdownFormatterBackend

__all__ = [
    "AliasSuggestion",
    "EndpointInfo",
    "FormatFileRequest",
    "FormatFileResponse",
    "PreviewFileRequest",
    "PreviewFileResponse",
    "ListMarkdownFilesRequest",
    "ListMarkdownFilesResponse",
    "MarkdownFormatterBackend",
]

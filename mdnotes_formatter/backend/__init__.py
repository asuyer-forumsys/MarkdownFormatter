"""Backend package for markdown formatter business logic.

This backend layer is intentionally UI-agnostic. Any frontend (CLI today,
GUI/web later) should call these backend endpoints instead of touching the
formatting internals directly.
"""

from .contracts import EndpointInfo, FormatFileRequest, FormatFileResponse
from .endpoints import MarkdownFormatterBackend

__all__ = [
    "EndpointInfo",
    "FormatFileRequest",
    "FormatFileResponse",
    "MarkdownFormatterBackend",
]

"""Typed request/response contracts for backend endpoints.

These dataclasses form a stable API boundary between frontend layers and the
backend implementation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AliasSuggestion:
    """Suggested opt-in alias produced by alias intelligence.

    Attributes:
        alias: Suggested alias text.
        reason: Human-readable reason for why this suggestion exists.
    """

    alias: str
    reason: str


@dataclass(frozen=True)
class FormatFileRequest:
    """Input payload for the mutating format-file backend endpoint.

    Attributes:
        path: Path string to an existing `.md` file that should be reformatted.
        selected_advanced_aliases: Optional user-selected opt-in aliases to add.
    """

    path: str
    selected_advanced_aliases: list[str] | None = None


@dataclass(frozen=True)
class FormatFileResponse:
    """Output payload from the mutating format-file backend endpoint.

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
class PreviewFileRequest:
    """Input payload for the preview endpoint.

    Attributes:
        path: Path string to an existing `.md` file.
        selected_advanced_aliases: Optional user-selected opt-in aliases to
            include in preview rendering.
    """

    path: str
    selected_advanced_aliases: list[str] | None = None


@dataclass(frozen=True)
class PreviewFileResponse:
    """Output payload for non-mutating formatting preview.

    Attributes:
        original_path: Source file path.
        updated_path: Path that would result after apply.
        renamed: Whether apply would rename the file.
        original_content: Current markdown text on disk.
        formatted_content: Rendered markdown after applying formatter rules.
        changed_left_lines: 1-indexed source line numbers involved in change.
        changed_right_lines: 1-indexed rendered line numbers involved in change.
        advanced_alias_suggestions: Optional alias suggestions (opt-in only).
    """

    original_path: str
    updated_path: str
    renamed: bool
    original_content: str
    formatted_content: str
    changed_left_lines: list[int]
    changed_right_lines: list[int]
    advanced_alias_suggestions: list[AliasSuggestion]


@dataclass(frozen=True)
class ListMarkdownFilesRequest:
    """Input payload for recursive markdown file listing.

    Attributes:
        root: Optional directory path to list under. When omitted, backend root
            is used.
    """

    root: str | None = None


@dataclass(frozen=True)
class ListMarkdownFilesResponse:
    """Output payload for markdown file listing.

    Attributes:
        root: Absolute resolved directory used for listing.
        files: Absolute markdown file paths under the root (excluding .bak).
    """

    root: str
    files: list[str]


@dataclass(frozen=True)
class EndpointInfo:
    """Describes one backend endpoint.

    Attributes:
        name: Stable endpoint identifier.
        method: Logical invocation style (`local-call` for now).
        summary: One-line human-readable endpoint purpose.
        request_type: Name of the request contract type.
        response_type: Name of the response contract type.
    """

    name: str
    method: str
    summary: str
    request_type: str
    response_type: str

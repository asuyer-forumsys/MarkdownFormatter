"""Backend endpoint implementations.

Design goals:
- Keep business logic callable by any frontend.
- Keep transport details out of this module.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path

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
from ..filename_rules import normalize_filename_stem
from ..formatter import build_formatted_output, format_markdown_file
from ..frontmatter_rules import suggest_advanced_aliases


class MarkdownFormatterBackend:
    """UI-agnostic backend endpoint surface for markdown formatting.

    Endpoint naming follows an `endpoint_*` convention so transport adapters can
    expose these methods as HTTP/RPC routes without changing core logic.
    """

    def __init__(self, root: Path | str | None = None):
        """Initialize backend with an optional filesystem root boundary.

        Args:
            root: Base directory all file operations must remain under.
                When omitted, backend operates in unrestricted mode (useful for
                CLI flows where absolute paths anywhere on disk are expected).
        """
        self._root = Path(root).resolve() if root is not None else None

    def endpoint_health(self) -> dict[str, str]:
        """Health endpoint for frontend readiness checks."""
        return {"status": "ok", "service": "mdnotes-formatter-backend"}

    def endpoint_list_endpoints(self) -> list[EndpointInfo]:
        """Return machine-readable metadata for available backend endpoints."""
        return [
            EndpointInfo(
                name="health",
                method="local-call",
                summary="Health check endpoint for frontend connectivity.",
                request_type="None",
                response_type="dict[str, str]",
            ),
            EndpointInfo(
                name="list_markdown_files",
                method="local-call",
                summary="Recursively list markdown files under a root directory.",
                request_type="ListMarkdownFilesRequest",
                response_type="ListMarkdownFilesResponse",
            ),
            EndpointInfo(
                name="preview_file",
                method="local-call",
                summary="Preview formatted output and changed lines without writing files.",
                request_type="PreviewFileRequest",
                response_type="PreviewFileResponse",
            ),
            EndpointInfo(
                name="format_file",
                method="local-call",
                summary="Format one markdown file, create backup, and rename if needed.",
                request_type="FormatFileRequest",
                response_type="FormatFileResponse",
            ),
        ]

    def endpoint_list_markdown_files(
        self,
        request: ListMarkdownFilesRequest,
    ) -> ListMarkdownFilesResponse:
        """List markdown files recursively under the requested root.

        Notes:
            - Returns absolute paths.
            - Excludes backup files (`*.md.bak`).
            - Access is restricted to backend root boundary.
        """
        default_root = self._root or Path.cwd().resolve()
        root = self._resolve_within_root(request.root or str(default_root), expect_dir=True)

        files = sorted(
            str(path)
            for path in root.rglob("*.md")
            if not path.name.endswith(".md.bak")
        )
        return ListMarkdownFilesResponse(root=str(root), files=files)

    def endpoint_preview_file(self, request: PreviewFileRequest) -> PreviewFileResponse:
        """Preview formatting result for one markdown file without writing.

        Returns full before/after content plus line indexes that changed, which
        frontend layers can use for diff-like highlighting.
        """
        file_path = self._resolve_within_root(request.path)
        original_content = file_path.read_text(encoding="utf-8")

        output = build_formatted_output(
            file_path,
            additional_aliases=request.selected_advanced_aliases or [],
        )
        left_lines, right_lines = self._compute_changed_line_sets(
            original=original_content,
            formatted=output.rendered_text,
        )

        normalized_stem = normalize_filename_stem(file_path.stem)
        suggestions = [
            AliasSuggestion(alias=item.alias, reason=item.reason)
            for item in suggest_advanced_aliases(normalized_stem)
        ]

        return PreviewFileResponse(
            original_path=str(file_path),
            updated_path=str(output.updated_path),
            renamed=output.renamed,
            original_content=original_content,
            formatted_content=output.rendered_text,
            changed_left_lines=left_lines,
            changed_right_lines=right_lines,
            advanced_alias_suggestions=suggestions,
        )

    def endpoint_format_file(self, request: FormatFileRequest) -> FormatFileResponse:
        """Format and normalize one markdown note file (mutating endpoint)."""
        original_path = self._resolve_within_root(request.path)
        updated_path = format_markdown_file(
            original_path,
            additional_aliases=request.selected_advanced_aliases or [],
        )

        return FormatFileResponse(
            original_path=str(original_path),
            updated_path=str(updated_path),
            backup_path=str(original_path.with_name(original_path.name + ".bak")),
            renamed=updated_path != original_path,
        )

    def _resolve_within_root(self, value: str, expect_dir: bool = False) -> Path:
        """Resolve `value` into an absolute path with optional root constraint."""
        raw = Path(value)

        if self._root is None:
            candidate = (Path.cwd() / raw).resolve() if not raw.is_absolute() else raw.resolve()
        else:
            candidate = (self._root / raw).resolve() if not raw.is_absolute() else raw.resolve()
            try:
                candidate.relative_to(self._root)
            except ValueError as exc:
                raise ValueError(f"Path '{value}' is outside backend root '{self._root}'.") from exc

        if expect_dir:
            if not candidate.exists() or not candidate.is_dir():
                raise FileNotFoundError(candidate)
        else:
            if not candidate.exists() or not candidate.is_file():
                raise FileNotFoundError(candidate)

        return candidate

    @staticmethod
    def _compute_changed_line_sets(original: str, formatted: str) -> tuple[list[int], list[int]]:
        """Compute changed line numbers between original and formatted text.

        Returns:
            A tuple: (`left_changed_lines`, `right_changed_lines`) with 1-indexed
            line numbers suitable for UI highlighting.
        """
        left_lines = original.splitlines()
        right_lines = formatted.splitlines()

        changed_left: set[int] = set()
        changed_right: set[int] = set()

        matcher = SequenceMatcher(a=left_lines, b=right_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in {"replace", "delete"}:
                changed_left.update(range(i1 + 1, i2 + 1))
            if tag in {"replace", "insert"}:
                changed_right.update(range(j1 + 1, j2 + 1))

        return sorted(changed_left), sorted(changed_right)

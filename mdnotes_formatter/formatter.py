"""Top-level file formatter orchestration.

This module centralizes markdown formatting workflows and exposes two modes:

1. Preview mode (no filesystem writes): `build_formatted_output`
2. Apply mode (writes/rename + backup): `format_markdown_file`
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .body_rules import normalize_body
from .filename_rules import normalize_filename_stem, stem_to_title
from .frontmatter_rules import build_frontmatter


@dataclass(frozen=True)
class FormattedOutput:
    """In-memory representation of a formatting result.

    Attributes:
        original_path: Source markdown file path.
        updated_path: Path where formatted content should live after apply.
        backup_path: Backup path that apply mode writes (`<original>.bak`).
        rendered_text: Full formatted markdown (frontmatter + body).
        renamed: Whether the normalized output path differs from source path.
    """

    original_path: Path
    updated_path: Path
    backup_path: Path
    rendered_text: str
    renamed: bool


def extract_frontmatter_and_body(text: str) -> tuple[str, str]:
    """Split markdown text into frontmatter and body.

    Returns an empty frontmatter string when no YAML frontmatter is present.
    """
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


def build_formatted_output(path: Path | str) -> FormattedOutput:
    """Build formatted markdown output without mutating the filesystem.

    Args:
        path: Path to an existing markdown file.

    Returns:
        A `FormattedOutput` with full rendered content and resulting paths.

    Raises:
        ValueError: If file extension is not `.md`.
        FileNotFoundError: If the requested file does not exist.
    """
    file_path = Path(path)

    if file_path.suffix.lower() != ".md":
        raise ValueError("Only .md files are supported")
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    original_text = file_path.read_text(encoding="utf-8")

    normalized_stem = normalize_filename_stem(file_path.stem)
    updated_path = file_path.with_name(f"{normalized_stem}.md")

    _, body = extract_frontmatter_and_body(original_text)
    title_h1 = stem_to_title(normalized_stem)

    new_frontmatter = build_frontmatter(normalized_stem)
    new_body = normalize_body(body.splitlines(), title_h1=title_h1)
    rendered_text = f"{new_frontmatter}\n{new_body}"

    return FormattedOutput(
        original_path=file_path,
        updated_path=updated_path,
        backup_path=file_path.with_name(file_path.name + ".bak"),
        rendered_text=rendered_text,
        renamed=updated_path != file_path,
    )


def format_markdown_file(path: Path | str) -> Path:
    """Format one markdown note file in place and return final path.

    Behavior:
    - Only `.md` files are accepted.
    - Always creates a `.bak` backup at the original path.
    - May rename the file if normalization changes the filename stem.
    - Rewrites frontmatter and body to meet formatting requirements.

    Args:
        path: Path to an existing markdown file.

    Returns:
        The final file path after any rename.
    """
    output = build_formatted_output(path)

    shutil.copy2(output.original_path, output.backup_path)

    if output.updated_path != output.original_path:
        output.original_path.unlink()

    output.updated_path.write_text(output.rendered_text, encoding="utf-8")
    return output.updated_path

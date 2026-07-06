"""Top-level file formatter orchestration.

This module handles file I/O and sequencing of rule modules:
1. validate input
2. create backup
3. normalize output path
4. normalize content (frontmatter + body)
5. write formatted markdown back to disk
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .body_rules import normalize_body
from .filename_rules import normalize_filename_stem, stem_to_title
from .frontmatter_rules import build_frontmatter


def extract_frontmatter_and_body(text: str) -> tuple[str, str]:
    """Split markdown text into frontmatter and body.

    Returns an empty frontmatter string when no YAML frontmatter is present.
    """
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


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
    file_path = Path(path)

    if file_path.suffix.lower() != ".md":
        raise ValueError("Only .md files are supported")
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    original_text = file_path.read_text(encoding="utf-8")

    backup_path = file_path.with_name(file_path.name + ".bak")
    shutil.copy2(file_path, backup_path)

    normalized_stem = normalize_filename_stem(file_path.stem)
    new_path = file_path.with_name(f"{normalized_stem}.md")

    _, body = extract_frontmatter_and_body(original_text)
    title_h1 = stem_to_title(normalized_stem)

    new_frontmatter = build_frontmatter(normalized_stem)
    new_body = normalize_body(body.splitlines(), title_h1=title_h1)
    final_text = f"{new_frontmatter}\n{new_body}"

    if new_path != file_path:
        file_path.unlink()

    new_path.write_text(final_text, encoding="utf-8")
    return new_path

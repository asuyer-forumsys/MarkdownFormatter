"""Markdown body normalization rules.

This module is intentionally focused on structure-level body transforms:
- removing pre-existing conflicting sections
- collecting topics from headings
- enforcing one H1
- normalizing paragraph wrapping
- preserving code fences and list blocks
- outputting consistent blank-line spacing between blocks
"""

from __future__ import annotations

import re
from typing import Iterable


def is_heading(line: str) -> bool:
    """Return True when ``line`` is a markdown heading (H1-H6)."""
    return bool(re.match(r"^#{1,6}\s+", line.strip()))


def is_h1(line: str) -> bool:
    """Return True when ``line`` is a top-level heading (H1)."""
    return bool(re.match(r"^#\s+", line.strip()))


def heading_text(line: str) -> str:
    """Strip heading markers and return heading display text."""
    return re.sub(r"^#{1,6}\s+", "", line.strip()).strip()


def is_list_item(line: str) -> bool:
    """Return True when ``line`` is an unordered or ordered markdown list item."""
    return bool(re.match(r"^\s*(?:[-*+]\s+|\d+\.\s+)", line))


def is_code_fence(line: str) -> bool:
    """Return True when ``line`` starts or ends a fenced code block."""
    stripped = line.strip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def collect_topics(lines: Iterable[str]) -> list[str]:
    """Collect unique topic labels from H2-H6 headings in source order."""
    topics: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{2,6}\s+", stripped):
            topic = heading_text(stripped)
            if topic and topic not in seen:
                seen.add(topic)
                topics.append(topic)

    return topics


def strip_existing_topics_section(lines: list[str]) -> list[str]:
    """Remove a leading `Topics covered` section if one already exists.

    This makes formatting idempotent and avoids duplicating the section when
    the formatter is run repeatedly.
    """
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx >= len(lines) or lines[idx].strip().lower() != "topics covered":
        return lines

    idx += 1
    while idx < len(lines) and is_list_item(lines[idx]):
        idx += 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    return lines[idx:]


def normalize_body(lines: list[str], title_h1: str) -> str:
    """Normalize markdown body to the required note format.

    Args:
        lines: Body lines excluding frontmatter.
        title_h1: Canonical title text to use for the sole H1.

    Returns:
        Normalized markdown body ending with a trailing newline.
    """
    lines = strip_existing_topics_section(lines)

    # Remove all existing H1 headings; we regenerate exactly one canonical H1.
    filtered = [line.rstrip("\n") for line in lines if not is_h1(line)]
    topics = collect_topics(filtered)

    blocks: list[str] = []
    paragraph_acc: list[str] = []
    code_acc: list[str] = []
    in_code = False
    idx = 0

    def flush_paragraph() -> None:
        """Collapse accumulated paragraph lines into one long line."""
        if not paragraph_acc:
            return

        text = " ".join(part.strip() for part in paragraph_acc if part.strip())
        if text:
            blocks.append(text)
        paragraph_acc.clear()

    while idx < len(filtered):
        line = filtered[idx]
        stripped = line.strip()

        if in_code:
            code_acc.append(line)
            if is_code_fence(line):
                blocks.append("\n".join(code_acc).strip("\n"))
                code_acc = []
                in_code = False
            idx += 1
            continue

        if is_code_fence(line):
            flush_paragraph()
            in_code = True
            code_acc = [line]
            idx += 1
            continue

        if not stripped:
            flush_paragraph()
            idx += 1
            continue

        if is_heading(line):
            flush_paragraph()
            blocks.append(stripped)
            idx += 1
            continue

        if is_list_item(line):
            flush_paragraph()
            list_block = [line.strip()]
            idx += 1
            while idx < len(filtered) and is_list_item(filtered[idx]):
                list_block.append(filtered[idx].strip())
                idx += 1
            blocks.append("\n".join(list_block))
            continue

        paragraph_acc.append(line)
        idx += 1

    flush_paragraph()

    # Recover unfinished code block text if the source had an unmatched fence.
    if in_code and code_acc:
        blocks.append("\n".join(code_acc).strip("\n"))

    intro = ["Topics covered"]
    intro.extend(f"- {topic}" for topic in topics)

    output_blocks = ["\n".join(intro), f"# {title_h1}"]
    output_blocks.extend(block for block in blocks if block.strip())

    # A single blank line between blocks => exactly one empty line separator.
    return "\n\n".join(output_blocks).strip() + "\n"

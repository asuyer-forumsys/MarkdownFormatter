from __future__ import annotations

import re
from pathlib import Path

import pytest

from mdnotes_formatter import format_markdown_file


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_filename_normalization_renames_to_capitalized_kebab(tmp_path: Path):
    src = _write(tmp_path / "My NOTE_about___CATS!!!.md", "body\n")

    updated = format_markdown_file(src)

    assert updated.name == "My-note-about-cats.md"
    assert updated.exists()
    assert (tmp_path / "My NOTE_about___CATS!!!.md.bak").exists()


@pytest.mark.parametrize(
    "raw_stem, expected",
    [
        ("alpha", "Alpha.md"),
        ("already-kebab", "Already-kebab.md"),
        ("MIXED Case___Name", "Mixed-case-name.md"),
        ("!!!", "Note.md"),
    ],
)
def test_filename_normalization_cases(tmp_path: Path, raw_stem: str, expected: str):
    src = _write(tmp_path / f"{raw_stem}.md", "x\n")

    updated = format_markdown_file(src)

    assert updated.name == expected


def test_frontmatter_aliases_include_only_title_and_lowercase_phrase(tmp_path: Path):
    src = _write(tmp_path / "Network-notes.md", "Plain text\n")

    updated = format_markdown_file(src)
    content = _read(updated)

    assert content.startswith("---\n")
    assert "aliases:" in content
    assert "- Network Notes" in content
    assert "- network notes" in content

    # No kebab alias or extra inflections.
    assert "- Network-notes" not in content
    assert "- network-notes" not in content
    assert "- Network note" not in content


def test_aliases_drop_numeric_tokens_and_do_not_include_numbers(tmp_path: Path):
    src = _write(tmp_path / "02-missing-topics-covered.md", "Plain text\n")

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "- Missing Topics Covered" in content
    assert "- missing topics covered" in content
    assert "- 02 missing topics covered" not in content

    alias_lines = [line.strip() for line in content.splitlines() if line.strip().startswith("- ")]
    assert alias_lines == ["- Missing Topics Covered", "- missing topics covered"]


def test_one_word_filename_does_not_duplicate_filename_as_alias(tmp_path: Path):
    src = _write(tmp_path / "Agents.md", "Plain text\n")

    updated = format_markdown_file(src)
    content = _read(updated)

    alias_lines = [line.strip() for line in content.splitlines() if line.strip().startswith("- ")]
    assert alias_lines == ["- agents"]


def test_existing_frontmatter_is_replaced_with_normalized_alias_frontmatter(tmp_path: Path):
    src = _write(
        tmp_path / "Storage-systems.md",
        """---
title: old
aliases: [legacy]
---

Old paragraph.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "title: old" not in content
    assert "legacy" not in content
    assert content.startswith("---\naliases:\n")


def test_body_starts_with_topics_covered_and_derived_topics(tmp_path: Path):
    src = _write(
        tmp_path / "Distributed-systems.md",
        """Intro text.

## Consensus
Explains leader election.

### Raft internals
Details.

## Fault tolerance
Notes.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    # Topics section appears before H1 and includes H2+ headings in source order.
    assert "\nTopics covered:\n- Consensus\n  - Raft internals\n- Fault tolerance\n\n# Distributed Systems\n" in content


def test_top_level_h1_is_after_topics_and_only_h1(tmp_path: Path):
    src = _write(
        tmp_path / "Cloud-architecture.md",
        """# Wrong One

## Intro
Some text.

# Wrong Two

## More
More text.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "\n# Cloud Architecture\n" in content
    assert content.count("\n# ") == 1
    assert content.index("Topics covered") < content.index("# Cloud Architecture")


def test_paragraphs_are_unwrapped_to_single_line(tmp_path: Path):
    src = _write(
        tmp_path / "Paragraph-wrapping.md",
        """This paragraph starts
on one line and continues
across several wrapped lines.

## Section
Second paragraph
also wraps.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "This paragraph starts on one line and continues across several wrapped lines." in content
    assert "Second paragraph also wraps." in content


def test_blank_line_spacing_between_headings_paragraphs_and_code_blocks(tmp_path: Path):
    src = _write(
        tmp_path / "Spacing-rules.md",
        """## Heading
Paragraph one.
```python
print('x')
```
Paragraph two.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    # Ensure canonical separators around major block boundaries.
    assert "# Spacing Rules\n\n## Heading\n\nParagraph one." in content
    assert "Paragraph one.\n\n```python" in content
    assert "```\n\nParagraph two." in content


def test_existing_topics_section_is_replaced_not_duplicated(tmp_path: Path):
    src = _write(
        tmp_path / "Topic-refresh.md",
        """Topics covered
- Wrong A
- Wrong B

# Wrong H1

## Actual Topic
Body text.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert content.count("Topics covered") == 1
    assert "- Actual Topic" in content
    assert "- Wrong A" not in content


def test_topics_covered_header_uses_colon_and_replaces_similar_existing_header(tmp_path: Path):
    src = _write(
        tmp_path / "Topic-variation.md",
        """TOPICS   covered :
- stale

## Real Topic
Body text.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "Topics covered:" in content
    assert content.count("Topics covered:") == 1
    assert "- stale" not in content
    assert "- Real Topic" in content


def test_topics_covered_list_indents_subsections_by_heading_depth(tmp_path: Path):
    src = _write(
        tmp_path / "Hierarchy-topics.md",
        """## Parent Topic
Details.

### Child Topic
Child details.

#### Grandchild Topic
Grandchild details.
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "Topics covered:\n- Parent Topic\n  - Child Topic\n    - Grandchild Topic\n" in content


def test_topics_deduplicate_duplicate_headings(tmp_path: Path):
    src = _write(
        tmp_path / "Dedup-topics.md",
        """## Repeat
one

## Repeat
two

### Repeat
three
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert content.count("- Repeat") == 1


def test_code_block_content_is_preserved_with_internal_newlines(tmp_path: Path):
    src = _write(
        tmp_path / "Code-preservation.md",
        """## Snippet

```python
x = 1
if x:
    print(x)
```
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "```python\nx = 1\nif x:\n    print(x)\n```" in content


def test_unmatched_code_fence_does_not_crash_and_is_preserved(tmp_path: Path):
    src = _write(
        tmp_path / "Unmatched-fence.md",
        """## Notes

```bash
echo hello
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "```bash\necho hello" in content


def test_equations_between_double_dollar_blocks_preserve_multiline_layout(tmp_path: Path):
    src = _write(
        tmp_path / "Math-layout.md",
        """## Formula

$$
a = b + c
d = e + f
$$
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "$$\na = b + c\nd = e + f\n$$" in content


def test_no_h2_headings_still_gets_topics_covered_header(tmp_path: Path):
    src = _write(tmp_path / "No-topics.md", "Just a paragraph.\n")

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "Topics covered:\n\n# No Topics\n" in content


def test_lists_are_preserved_as_list_blocks(tmp_path: Path):
    src = _write(
        tmp_path / "List-behavior.md",
        """## Items
- alpha
- beta

1. first
2. second
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    assert "- alpha\n- beta" in content
    assert "1. first\n2. second" in content


def test_combined_multi_requirement_input_gets_fully_normalized(tmp_path: Path):
    src = _write(
        tmp_path / "my BAD__note FILE!!.md",
        """---
foo: bar
---

Topics covered
- stale topic

# old heading

This paragraph is
wrapped badly.

## Real Topic
text line one
text line two

```python
print('ok')
```

# another old heading
""",
    )

    updated = format_markdown_file(src)
    content = _read(updated)

    # Renaming + backup
    assert updated.name == "My-bad-note-file.md"
    assert (tmp_path / "my BAD__note FILE!!.md.bak").exists()

    # Frontmatter rebuilt
    assert content.startswith("---\naliases:\n")
    assert "foo: bar" not in content

    # Body structure and normalization
    assert "Topics covered:\n- Real Topic\n\n# My Bad Note File\n" in content
    assert content.count("\n# ") == 1
    assert "This paragraph is wrapped badly." in content
    assert "text line one text line two" in content
    assert "```python\nprint('ok')\n```" in content


def test_formatter_is_idempotent_for_output_content(tmp_path: Path):
    src = _write(
        tmp_path / "Idempotence-check.md",
        """## Topic
line one
line two
""",
    )

    first_path = format_markdown_file(src)
    first_content = _read(first_path)

    second_path = format_markdown_file(first_path)
    second_content = _read(second_path)

    assert first_path == second_path
    assert first_content == second_content


def test_non_markdown_extension_raises_value_error(tmp_path: Path):
    txt = _write(tmp_path / "note.txt", "hello")

    with pytest.raises(ValueError):
        format_markdown_file(txt)


def test_missing_file_raises_file_not_found(tmp_path: Path):
    missing = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError):
        format_markdown_file(missing)


def test_h1_matches_filename_title_case(tmp_path: Path):
    src = _write(tmp_path / "Zero-trust-security.md", "## Topic\nBody\n")

    updated = format_markdown_file(src)
    content = _read(updated)

    assert re.search(r"\n# Zero Trust Security\n", content)


def test_h1_ignores_leading_and_trailing_numeric_filename_tokens(tmp_path: Path):
    src = _write(tmp_path / "01-agent-patterns-2024.md", "## Topic\nBody\n")

    updated = format_markdown_file(src)
    content = _read(updated)

    assert re.search(r"\n# Agent Patterns\n", content)
    assert "# 01 Agent Patterns 2024" not in content

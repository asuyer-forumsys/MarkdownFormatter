from pathlib import Path

from mdnotes_formatter import format_markdown_file


def test_formats_markdown_and_creates_backup(tmp_path: Path):
    src = tmp_path / "my NOTE_about_dogs.md"
    src.write_text(
        """---
title: old
---
# wrong h1

Dogs are
awesome pets that help
people.

## Care
Feed daily.

## Training
Be consistent.

```python
print('hi')
```
""",
        encoding="utf-8",
    )

    updated_path = format_markdown_file(src)

    # Renamed path should be kebab-case with first char capitalized.
    assert updated_path.name == "My-note-about-dogs.md"
    assert updated_path.exists()

    # Backup should be created at original path + .bak
    backup_path = tmp_path / "my NOTE_about_dogs.md.bak"
    assert backup_path.exists()
    assert "# wrong h1" in backup_path.read_text(encoding="utf-8")

    content = updated_path.read_text(encoding="utf-8")

    # Frontmatter with aliases
    assert content.startswith("---\n")
    assert "aliases:" in content
    assert "- My Note About Dogs" in content
    assert "- my note about dogs" in content
    assert "- My note about dog" not in content
    assert "- My notes about dogs" not in content

    # Topics covered then single H1 title
    assert "\nTopics covered\n" in content
    assert "- Care" in content
    assert "- Training" in content
    assert "\n# My Note About Dogs\n" in content
    assert content.count("\n# ") == 1

    # Paragraph should be unwrapped to one line.
    assert "Dogs are awesome pets that help people." in content

    # Heading/code/paragraph separated by exactly one blank line at least for key transitions.
    assert "Topics covered\n- Care\n- Training\n\n# My Note About Dogs" in content
    assert "Be consistent.\n\n```python" in content


def test_keeps_filename_when_already_normalized(tmp_path: Path):
    src = tmp_path / "My-topic.md"
    src.write_text("Simple text\n", encoding="utf-8")

    updated_path = format_markdown_file(src)

    assert updated_path == src
    assert src.with_suffix(".md.bak").exists()

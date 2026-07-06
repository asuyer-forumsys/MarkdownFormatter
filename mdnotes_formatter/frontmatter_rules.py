"""Frontmatter generation rules for markdown notes.

This module focuses on alias generation so file concepts are easy to link via
wiki-links (e.g. [[my note about dogs]]).
"""

from __future__ import annotations

import re

from .filename_rules import pluralize, singularize, stem_to_title


def _yaml_item(value: str) -> str:
    """Return a YAML-safe scalar for list usage.

    Values with special YAML-significant characters are double-quoted.
    """
    if re.search(r"[:\[\]{}#,]|^\s|\s$", value):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def build_frontmatter(normalized_stem: str) -> str:
    """Build YAML frontmatter containing convenience aliases.

    Included alias variants:
    - title-cased phrase
    - lower sentence-cased phrase
    - singular and plural phrase variants
    - note/notes word swaps
    - kebab-case normalized stem (original and lowercase)
    """
    spaced = normalized_stem.replace("-", " ")
    title_case = stem_to_title(normalized_stem)
    singular = singularize(spaced)
    plural = pluralize(spaced)

    # Optional concept expansion: treat 'note'/'notes' as interchangeable.
    note_plural_variant = re.sub(r"\bnote\b", "notes", spaced, flags=re.IGNORECASE)
    note_singular_variant = re.sub(r"\bnotes\b", "note", spaced, flags=re.IGNORECASE)

    aliases: list[str] = []
    for alias in [
        title_case,
        spaced,
        singular,
        plural,
        note_plural_variant,
        note_singular_variant,
        normalized_stem,
        normalized_stem.lower(),
    ]:
        if alias and alias not in aliases:
            aliases.append(alias)

    alias_lines = "\n".join(f"  - {_yaml_item(alias)}" for alias in aliases)
    return f"---\naliases:\n{alias_lines}\n---\n"

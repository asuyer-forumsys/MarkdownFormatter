"""Frontmatter generation rules for markdown notes.

This module focuses on alias generation so note concepts are easy to link via
wiki-links (e.g. [[missing topics covered]]).
"""

from __future__ import annotations

import re

from .filename_rules import stem_to_title


def _yaml_item(value: str) -> str:
    """Return a YAML-safe scalar for list usage."""
    if re.search(r"[:\[\]{}#,]|^\s|\s$", value):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _stem_without_numeric_tokens(normalized_stem: str) -> str:
    """Return normalized stem with numeric-only tokens removed.

    Example:
        ``"02-missing-topics-covered" -> "missing-topics-covered"``
    """
    tokens = [token for token in normalized_stem.split("-") if token and not token.isdigit()]
    return "-".join(tokens) if tokens else "note"


def build_frontmatter(normalized_stem: str) -> str:
    """Build YAML frontmatter containing wiki-link convenience aliases.

    The alias strategy is intentionally conservative:
    - one title-case phrase alias
    - one lowercase phrase alias
    - no numeric tokens
    - no kebab-case filename aliases
    """
    stem_for_aliases = _stem_without_numeric_tokens(normalized_stem)
    title_alias = stem_to_title(stem_for_aliases)
    lower_alias = title_alias.lower()

    aliases = [title_alias, lower_alias]

    alias_lines = "\n".join(f"  - {_yaml_item(alias)}" for alias in aliases)
    return f"---\naliases:\n{alias_lines}\n---\n"

"""Frontmatter generation and alias intelligence for markdown notes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .filename_rules import stem_to_title


_EQUIVALENT_TERMS: dict[str, list[str]] = {
    "oxford comma": ["serial comma"],
    "serial comma": ["oxford comma"],
    "llm": ["large language model"],
    "large language model": ["llm"],
    "ai": ["artificial intelligence"],
    "artificial intelligence": ["ai"],
}

_STOPWORDS = {"a", "an", "and", "or", "of", "the", "to", "for", "in", "on", "with"}


@dataclass(frozen=True)
class AdvancedAliasSuggestion:
    """One suggested alias candidate and its generation reason."""

    alias: str
    reason: str


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


def _normalize_alias_text(value: str) -> str:
    """Normalize alias text for consistent dedupe and rendering."""
    collapsed = re.sub(r"\s+", " ", value.strip())
    return collapsed


def _strip_numeric_tokens_from_phrase(value: str) -> str:
    """Remove standalone numeric tokens from phrase aliases."""
    tokens = [token for token in value.split() if not token.isdigit()]
    return " ".join(tokens).strip()


def build_base_aliases(normalized_stem: str) -> list[str]:
    """Return default always-on aliases.

    Base aliases are intentionally conservative:
    - multi-word notes: title-case phrase + lowercase phrase
    - single-word notes: lowercase phrase only (avoids filename duplication)
    """
    stem_for_aliases = _stem_without_numeric_tokens(normalized_stem)
    title_alias = stem_to_title(stem_for_aliases)
    lower_alias = title_alias.lower()

    if len(title_alias.split()) == 1:
        return [lower_alias]

    return [title_alias, lower_alias]


def suggest_advanced_aliases(normalized_stem: str) -> list[AdvancedAliasSuggestion]:
    """Suggest opt-in advanced aliases (never auto-applied).

    Current strategy:
    - acronym generation from multi-word titles
    - curated equivalent terminology map (e.g., oxford/serial comma)
    """
    base_aliases = build_base_aliases(normalized_stem)
    if not base_aliases:
        return []

    stem_for_aliases = _stem_without_numeric_tokens(normalized_stem)
    title_alias = stem_to_title(stem_for_aliases)
    lower_alias = title_alias.lower()

    suggestions: list[AdvancedAliasSuggestion] = []
    seen: set[str] = set(base_aliases)

    words = [word for word in lower_alias.split() if word and word not in _STOPWORDS]
    acronym = "".join(word[0].upper() for word in words if word[0].isalpha())
    if len(acronym) >= 2 and acronym not in seen:
        suggestions.append(
            AdvancedAliasSuggestion(
                alias=acronym,
                reason="Acronym built from the note title words.",
            ),
        )
        seen.add(acronym)

    for equivalent in _EQUIVALENT_TERMS.get(lower_alias, []):
        for alias_variant in [equivalent.title(), equivalent.lower()]:
            normalized = alias_variant
            if normalized in seen:
                continue
            suggestions.append(
                AdvancedAliasSuggestion(
                    alias=alias_variant,
                    reason=f"Common alternative term for '{title_alias}'.",
                ),
            )
            seen.add(normalized)

    return suggestions


def build_frontmatter(normalized_stem: str, additional_aliases: list[str] | None = None) -> str:
    """Build YAML frontmatter containing aliases.

    Args:
        normalized_stem: Canonical normalized filename stem.
        additional_aliases: Optional user-selected opt-in aliases.
    """
    aliases: list[str] = []
    seen: set[str] = set()

    for alias in [*build_base_aliases(normalized_stem), *(additional_aliases or [])]:
        candidate = _normalize_alias_text(alias)
        candidate = _strip_numeric_tokens_from_phrase(candidate)
        if not candidate:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        aliases.append(candidate)

    alias_lines = "\n".join(f"  - {_yaml_item(alias)}" for alias in aliases)
    return f"---\naliases:\n{alias_lines}\n---\n"

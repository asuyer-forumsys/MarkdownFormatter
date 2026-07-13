"""Filename normalization and simple inflection helpers.

This module contains small utilities used by the formatter to derive:
- normalized file names
- title text from file stems
- singular/plural alias variants
"""

from __future__ import annotations

import re


def _strip_edge_numeric_tokens(tokens: list[str]) -> list[str]:
    """Return tokens with leading/trailing numeric-only tokens removed.

    Numeric prefixes/suffixes are often ordering artifacts in filenames and are
    not useful in natural-language titles.
    """
    if not tokens:
        return tokens

    start = 0
    end = len(tokens)

    while start < end and tokens[start].isdigit():
        start += 1
    while end > start and tokens[end - 1].isdigit():
        end -= 1

    stripped = tokens[start:end]
    return stripped if stripped else tokens


def normalize_filename_stem(stem: str) -> str:
    """Return normalized kebab-case stem with first character capitalized.

    The normalization rules are intentionally conservative:
    1. Convert underscores/hyphens to spaces.
    2. Remove non-alphanumeric characters.
    3. Lowercase all words.
    4. Join words with hyphens.
    5. Capitalize only the first character of the full stem.

    Args:
        stem: Raw filename stem (without extension).

    Returns:
        Normalized stem. Falls back to ``"Note"`` when nothing is usable.
    """
    text = stem.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^A-Za-z0-9\s]", " ", text)
    words = [word.lower() for word in text.split() if word]
    if not words:
        return "Note"

    kebab = "-".join(words)
    return kebab[:1].upper() + kebab[1:]


def stem_to_title(stem: str) -> str:
    """Convert kebab stem into title-cased, space-separated text.

    Example:
        ``"my-note-about-dogs" -> "My Note About Dogs"``
    """
    tokens = [word for word in stem.split("-") if word]
    tokens = _strip_edge_numeric_tokens(tokens)
    return " ".join(word.capitalize() for word in tokens)


def singularize(phrase: str) -> str:
    """Return a basic singular form of a phrase.

    Only the final word is transformed and this is intentionally heuristic
    (not a full linguistic inflection engine).
    """
    words = phrase.split()
    if not words:
        return phrase

    last = words[-1]
    if last.endswith("ies") and len(last) > 3:
        words[-1] = last[:-3] + "y"
    elif last.endswith("ses") and len(last) > 3:
        words[-1] = last[:-2]
    elif last.endswith("s") and len(last) > 1 and not last.endswith("ss"):
        words[-1] = last[:-1]
    return " ".join(words)


def pluralize(phrase: str) -> str:
    """Return a basic plural form of a phrase.

    Only the final word is transformed and this is intentionally heuristic.
    """
    words = phrase.split()
    if not words:
        return phrase

    last = words[-1]
    lower = last.lower()

    if lower.endswith("s"):
        return phrase
    if lower.endswith("y") and len(last) > 1 and lower[-2] not in "aeiou":
        words[-1] = last[:-1] + "ies"
    elif lower.endswith(("x", "z", "ch", "sh")):
        words[-1] = last + "es"
    else:
        words[-1] = last + "s"

    return " ".join(words)

from __future__ import annotations

from mdnotes_formatter.frontmatter_rules import (
    build_base_aliases,
    build_frontmatter,
    suggest_advanced_aliases,
)


def test_build_base_aliases_returns_title_and_lowercase_only():
    aliases = build_base_aliases("02-missing-topics-covered")
    assert aliases == ["Missing Topics Covered", "missing topics covered"]


def test_advanced_alias_suggestions_include_acronym_and_equivalent_terms():
    oxford_suggestions = suggest_advanced_aliases("Oxford-comma")
    oxford_aliases = {item.alias for item in oxford_suggestions}

    assert {"OC", "Serial Comma", "serial comma"}.issubset(oxford_aliases)


def test_advanced_alias_suggestions_not_auto_applied_without_user_selection():
    rendered = build_frontmatter("Oxford-comma")

    assert "- Oxford Comma" in rendered
    assert "- oxford comma" in rendered
    assert "- Serial Comma" not in rendered
    assert "- serial comma" not in rendered


def test_build_frontmatter_includes_selected_opt_in_advanced_aliases():
    rendered = build_frontmatter(
        "Oxford-comma",
        additional_aliases=["Serial Comma", "serial comma"],
    )

    assert "- Oxford Comma" in rendered
    assert "- oxford comma" in rendered
    assert "- Serial Comma" in rendered
    assert "- serial comma" in rendered

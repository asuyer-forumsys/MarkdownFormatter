from __future__ import annotations

import json
from pathlib import Path

import pytest

from mdnotes_formatter.backend import (
    FormatFileRequest,
    ListMarkdownFilesRequest,
    MarkdownFormatterBackend,
    PreviewFileRequest,
)
from mdnotes_formatter.cli import build_parser, main as cli_main


def test_backend_list_endpoints_contains_web_relevant_endpoints():
    backend = MarkdownFormatterBackend()

    endpoints = backend.endpoint_list_endpoints()
    names = {endpoint.name for endpoint in endpoints}

    assert {"health", "list_markdown_files", "preview_file", "format_file"}.issubset(names)


def test_backend_format_file_response_contains_paths_and_rename_flag(tmp_path: Path):
    source = tmp_path / "my NOTE.md"
    source.write_text("## Topic\nline one\nline two\n", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)
    response = backend.endpoint_format_file(FormatFileRequest(path=str(source)))

    assert response.original_path == str(source)
    assert response.updated_path.endswith("My-note.md")
    assert response.backup_path.endswith("my NOTE.md.bak")
    assert response.renamed is True


def test_backend_preview_file_returns_before_after_and_changed_lines(tmp_path: Path):
    source = tmp_path / "preview NOTE.md"
    source.write_text("## Topic\nline one\nline two\n", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)
    preview = backend.endpoint_preview_file(PreviewFileRequest(path=str(source)))

    assert preview.original_path == str(source)
    assert preview.updated_path.endswith("Preview-note.md")
    assert preview.renamed is True
    assert "line one\nline two" in preview.original_content
    assert "line one line two" in preview.formatted_content
    assert len(preview.changed_left_lines) > 0
    assert len(preview.changed_right_lines) > 0
    assert isinstance(preview.advanced_alias_suggestions, list)


def test_backend_preview_includes_opt_in_advanced_alias_suggestions(tmp_path: Path):
    source = tmp_path / "Oxford-comma.md"
    source.write_text("## Topic\nline one\n", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)
    preview = backend.endpoint_preview_file(PreviewFileRequest(path=str(source)))

    aliases = {item.alias for item in preview.advanced_alias_suggestions}
    assert {"Serial Comma", "serial comma"}.issubset(aliases)


def test_backend_format_file_can_apply_selected_opt_in_advanced_aliases(tmp_path: Path):
    source = tmp_path / "Oxford-comma.md"
    source.write_text("## Topic\nline one\n", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)
    response = backend.endpoint_format_file(
        FormatFileRequest(
            path=str(source),
            selected_advanced_aliases=["Serial Comma", "serial comma"],
        ),
    )

    rendered = Path(response.updated_path).read_text(encoding="utf-8")
    assert "- Serial Comma" in rendered
    assert "- serial comma" in rendered


def test_backend_preview_file_for_single_word_filename_returns_success(tmp_path: Path):
    source = tmp_path / "Agents.md"
    source.write_text("## Topic\nBody\n", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)
    preview = backend.endpoint_preview_file(PreviewFileRequest(path=str(source)))

    assert preview.original_path == str(source)
    assert preview.updated_path == str(source)
    assert preview.advanced_alias_suggestions == []


def test_backend_list_markdown_files_filters_md_only_and_excludes_bak(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "a.md.bak").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.md").write_text("x", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)
    listed = backend.endpoint_list_markdown_files(ListMarkdownFilesRequest())

    assert listed.root == str(tmp_path.resolve())
    assert str((tmp_path / "a.md").resolve()) in listed.files
    assert str((nested / "c.md").resolve()) in listed.files
    assert not any(path.endswith(".md.bak") for path in listed.files)


def test_backend_rejects_paths_outside_root(tmp_path: Path):
    outside = tmp_path.parent / "outside.md"
    outside.write_text("x", encoding="utf-8")

    backend = MarkdownFormatterBackend(root=tmp_path)

    with pytest.raises(ValueError):
        backend.endpoint_preview_file(PreviewFileRequest(path=str(outside)))


def test_cli_endpoints_command_prints_json_catalog(capsys):
    exit_code = cli_main(["endpoints"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert any(endpoint["name"] == "preview_file" for endpoint in payload)


def test_cli_health_command_returns_backend_health_json(capsys):
    exit_code = cli_main(["health"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"


def test_cli_format_command_invokes_backend_and_prints_updated_path(tmp_path: Path, capsys):
    source = tmp_path / "messy NOTE.md"
    source.write_text("## Topic\nwrapped\nline\n", encoding="utf-8")

    exit_code = cli_main(["format", str(source)])

    captured = capsys.readouterr()
    updated_path = captured.out.strip()

    assert exit_code == 0
    assert updated_path.endswith("Messy-note.md")


def test_cli_legacy_single_argument_mode_is_still_supported(tmp_path: Path, capsys):
    source = tmp_path / "legacy NOTE.md"
    source.write_text("## Topic\nhello\nworld\n", encoding="utf-8")

    exit_code = cli_main([str(source)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip().endswith("Legacy-note.md")


def test_cli_parser_supports_web_command():
    parser = build_parser()
    args = parser.parse_args(["web", "--host", "0.0.0.0", "--port", "9999"])

    assert args.command == "web"
    assert args.host == "0.0.0.0"
    assert args.port == 9999

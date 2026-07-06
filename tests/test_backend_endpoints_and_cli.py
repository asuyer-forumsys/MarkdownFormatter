from __future__ import annotations

import json
from pathlib import Path

from mdnotes_formatter.backend import FormatFileRequest, MarkdownFormatterBackend
from mdnotes_formatter.cli import main as cli_main


def test_backend_list_endpoints_contains_health_and_format_file():
    backend = MarkdownFormatterBackend()

    endpoints = backend.endpoint_list_endpoints()
    names = {endpoint.name for endpoint in endpoints}

    assert "health" in names
    assert "format_file" in names


def test_backend_format_file_response_contains_paths_and_rename_flag(tmp_path: Path):
    source = tmp_path / "my NOTE.md"
    source.write_text("## Topic\nline one\nline two\n", encoding="utf-8")

    backend = MarkdownFormatterBackend()
    response = backend.endpoint_format_file(FormatFileRequest(path=str(source)))

    assert response.original_path == str(source)
    assert response.updated_path.endswith("My-note.md")
    assert response.backup_path.endswith("my NOTE.md.bak")
    assert response.renamed is True


def test_cli_endpoints_command_prints_json_catalog(capsys):
    exit_code = cli_main(["endpoints"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert any(endpoint["name"] == "format_file" for endpoint in payload)


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

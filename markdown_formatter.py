"""Backward-compatible script entrypoint.

This thin wrapper preserves the original command:
    python3 markdown_formatter.py <path>

Internally, logic now lives in the modular `mdnotes_formatter` package.
"""

from mdnotes_formatter import format_markdown_file
from mdnotes_formatter.cli import main

__all__ = ["format_markdown_file", "main"]


if __name__ == "__main__":
    raise SystemExit(main())

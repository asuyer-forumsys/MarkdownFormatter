"""Command-line entrypoints for the markdown note formatter."""

from __future__ import annotations

import argparse

from .formatter import format_markdown_file


def build_parser() -> argparse.ArgumentParser:
    """Create and return CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Format markdown notes to a standard structure.",
    )
    parser.add_argument("path", help="Path to the markdown file")
    return parser


def main() -> int:
    """Run CLI formatter command and print final path."""
    parser = build_parser()
    args = parser.parse_args()

    updated_path = format_markdown_file(args.path)
    print(str(updated_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Public package interface for the markdown note formatter.

Import from this module when you want to format a single markdown file from
Python code.
"""

from .formatter import format_markdown_file

__all__ = ["format_markdown_file"]

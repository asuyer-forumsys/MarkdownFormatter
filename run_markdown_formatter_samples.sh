#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-sample_markdown_inputs}"

if [[ ! -d "$INPUT_DIR" ]]; then
  echo "Input directory not found: $INPUT_DIR" >&2
  exit 1
fi

echo "Running markdown formatter on: $INPUT_DIR"

while IFS= read -r file; do
  echo "Formatting: $file"
  python3 markdown_formatter.py "$file"
done < <(find "$INPUT_DIR" -type f -name '*.md' ! -name 'README.md' | sort)

echo
echo "Done. Current markdown files:"
find "$INPUT_DIR" -type f -name '*.md' | sort

echo
echo "Backup files created (.bak):"
find "$INPUT_DIR" -type f -name '*.bak' | sort

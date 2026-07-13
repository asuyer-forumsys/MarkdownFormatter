#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-sample_markdown_inputs}"

if [[ ! -d "$INPUT_DIR" ]]; then
  echo "Input directory not found: $INPUT_DIR" >&2
  exit 1
fi

echo "Resetting markdown files from backups (.bak) in: $INPUT_DIR"
while IFS= read -r bak_file; do
  original_file="${bak_file%.bak}"
  cp "$bak_file" "$original_file"
  echo "Restored: $original_file"
done < <(find "$INPUT_DIR" -type f -name '*.md.bak' | sort)

echo
echo "Running markdown formatter on: $INPUT_DIR"

while IFS= read -r file; do
  echo "Formatting: $file"
  python3 -m mdnotes_formatter.cli format "$file"
done < <(find "$INPUT_DIR" -type f -name '*.md' ! -name 'README.md' | sort)

echo
echo "Done. Current markdown files:"
find "$INPUT_DIR" -type f -name '*.md' | sort

echo
echo "Backup files created (.bak):"
find "$INPUT_DIR" -type f -name '*.bak' | sort

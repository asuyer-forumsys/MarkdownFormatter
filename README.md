# mdnotes-formatter

A modular Python formatter for markdown note files.

## Environment setup (pinned versions)

Use a local virtual environment and the pinned lock file to get consistent
dependency versions across machines.

### Option A: one-command setup

```bash
chmod +x setup_venv.sh
./setup_venv.sh
source .venv/bin/activate
```

### Option B: manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
python -m pip install -e .
```

### Verify the environment

```bash
python -m pytest -q
```

## Run as a script

```bash
python3 markdown_formatter.py path/to/note.md
```

## Run as a module

```bash
python3 -m mdnotes_formatter.cli path/to/note.md
```

## Frontend / backend architecture

- **Backend**: `mdnotes_formatter.backend`
  - Endpoint contracts: `mdnotes_formatter/backend/contracts.py`
  - Endpoint handlers: `mdnotes_formatter/backend/endpoints.py`
- **Frontend (CLI)**: `mdnotes_formatter/cli.py`
  - Invokes backend endpoints only (no formatting logic in CLI layer).

Backend endpoint reference: `docs/backend-endpoints.md`

### CLI frontend commands

```bash
# Format a file via backend endpoint
python3 -m mdnotes_formatter.cli format path/to/note.md

# List endpoint catalog (JSON)
python3 -m mdnotes_formatter.cli endpoints

# Health check endpoint
python3 -m mdnotes_formatter.cli health

# Start local web UI frontend
python3 -m mdnotes_formatter.cli web
```

Backward compatibility is preserved:

```bash
python3 -m mdnotes_formatter.cli path/to/note.md
python3 markdown_formatter.py path/to/note.md
```

## Install editable + console script (optional)

```bash
python3 -m pip install -e .
mdnotes-format path/to/note.md
```

## Project structure

- `mdnotes_formatter/filename_rules.py` — filename normalization and inflection helpers
- `mdnotes_formatter/frontmatter_rules.py` — frontmatter and alias generation
- `mdnotes_formatter/body_rules.py` — body normalization and spacing rules
- `mdnotes_formatter/formatter.py` — file I/O orchestration used by backend endpoints
- `mdnotes_formatter/backend/contracts.py` — backend request/response endpoint contracts
- `mdnotes_formatter/backend/endpoints.py` — backend endpoint handlers
- `mdnotes_formatter/cli.py` — frontend command-line interface that invokes backend endpoints
- `mdnotes_formatter/web/app.py` — local web server adapter exposing backend endpoints via HTTP
- `mdnotes_formatter/web/static/` — web UI frontend assets (HTML/CSS/JS)
- `docs/backend-endpoints.md` — backend endpoint reference documentation

## Web UI frontend

Start the local server:

```bash
python3 -m mdnotes_formatter.cli web --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765` in your browser.

Features:
- Graphical markdown file explorer (backed by backend file-list endpoint)
- Side-by-side preview: original (left) vs formatted output (right)
- Diff-like changed line highlighting on both sides
- Syntax-highlighted markdown code view
- **Format** button that applies changes (writes file + backup, rename if needed)

## Requirement-to-test traceability

This table maps each requested behavior to concrete pytest coverage.

| Requirement | Primary tests | Additional combo/edge tests |
|---|---|---|
| Filename must be kebab-case with only first letter capitalized (except proper nouns by user editing later) | `test_filename_normalization_renames_to_capitalized_kebab`, `test_filename_normalization_cases`, `test_keeps_filename_when_already_normalized` | `test_combined_multi_requirement_input_gets_fully_normalized` |
| Frontmatter defines convenience aliases (spaced filename, singular/plural, common variants) | `test_frontmatter_aliases_include_spaced_singular_plural_and_kebab`, `test_existing_frontmatter_is_replaced_with_normalized_alias_frontmatter` | `test_formats_markdown_and_creates_backup`, `test_combined_multi_requirement_input_gets_fully_normalized` |
| Body begins with `Topics covered` + bullet list of topics | `test_body_starts_with_topics_covered_and_derived_topics`, `test_no_h2_headings_still_gets_topics_covered_header` | `test_existing_topics_section_is_replaced_not_duplicated`, `test_topics_deduplicate_duplicate_headings` |
| Top-level H1 appears after Topics covered, matches filename title with spaces, and is the only H1 | `test_top_level_h1_is_after_topics_and_only_h1`, `test_h1_matches_filename_title_case` | `test_formats_markdown_and_creates_backup`, `test_combined_multi_requirement_input_gets_fully_normalized` |
| No line breaks in middle of paragraphs (paragraphs become one long line) | `test_paragraphs_are_unwrapped_to_single_line` | `test_combined_multi_requirement_input_gets_fully_normalized` |
| One blank line surrounding each paragraph, heading, and code block | `test_blank_line_spacing_between_headings_paragraphs_and_code_blocks` | `test_formats_markdown_and_creates_backup` |
| Tool modifies/renames in place and creates `.bak` backup of original | `test_formats_markdown_and_creates_backup`, `test_filename_normalization_renames_to_capitalized_kebab`, `test_keeps_filename_when_already_normalized` | `test_combined_multi_requirement_input_gets_fully_normalized` |

### Edge and robustness tests

- Code fence handling: `test_code_block_content_is_preserved_with_internal_newlines`, `test_unmatched_code_fence_does_not_crash_and_is_preserved`
- List preservation: `test_lists_are_preserved_as_list_blocks`
- Idempotence: `test_formatter_is_idempotent_for_output_content`
- Error handling: `test_non_markdown_extension_raises_value_error`, `test_missing_file_raises_file_not_found`

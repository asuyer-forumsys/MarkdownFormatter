# Backend endpoint documentation

This document describes the backend endpoint surface consumed by both:

- CLI frontend (`mdnotes_formatter/cli.py`)
- Web UI frontend (`mdnotes_formatter/web/app.py`)

## Backend class

`mdnotes_formatter.backend.endpoints.MarkdownFormatterBackend`

Invocation style is currently `local-call` (direct Python method calls), but
endpoint names/contracts are stable so they can be adapted to HTTP/RPC later.

## Endpoint catalog

### `health`

- **Handler:** `endpoint_health()`
- **Request:** none
- **Response:**

```json
{
  "status": "ok",
  "service": "mdnotes-formatter-backend"
}
```

### `list_markdown_files`

- **Handler:** `endpoint_list_markdown_files(request: ListMarkdownFilesRequest)`
- **Request contract:**

```json
{
  "root": "optional/path"
}
```

- **Response contract:**

```json
{
  "root": "/absolute/resolved/root",
  "files": [
    "/absolute/path/to/a.md",
    "/absolute/path/to/nested/b.md"
  ]
}
```

Notes:
- Lists markdown files recursively.
- Excludes `*.md.bak`.
- Access is constrained to backend root.

### `preview_file`

- **Handler:** `endpoint_preview_file(request: PreviewFileRequest)`
- **Request contract:**

```json
{
  "path": "/absolute/or/relative/path/to/file.md"
}
```

- **Response contract:**

```json
{
  "original_path": "/path/original.md",
  "updated_path": "/path/Updated-file.md",
  "renamed": true,
  "original_content": "...",
  "formatted_content": "...",
  "changed_left_lines": [1, 2, 7],
  "changed_right_lines": [1, 2, 9]
}
```

Notes:
- Non-mutating endpoint.
- Designed for diff-like preview UI.

### `format_file`

- **Handler:** `endpoint_format_file(request: FormatFileRequest)`
- **Request contract:**

```json
{
  "path": "/absolute/or/relative/path/to/file.md"
}
```

- **Response contract:**

```json
{
  "original_path": "/path/original.md",
  "updated_path": "/path/Updated-file.md",
  "backup_path": "/path/original.md.bak",
  "renamed": true
}
```

Side effects:
- Writes formatted markdown content.
- Creates backup `.bak` file.
- May rename the source file.

## Error behavior

The following endpoint methods may raise:

- `ValueError`
  - Non-`.md` file
  - Attempt to access path outside backend root
- `FileNotFoundError`
  - Missing path or invalid root directory

## Web adapter routes

The local web server (`mdnotes_formatter/web/app.py`) maps these endpoints to:

- `GET /api/health` -> `health`
- `GET /api/endpoints` -> endpoint metadata catalog
- `GET /api/files?root=...` -> `list_markdown_files`
- `POST /api/preview` -> `preview_file`
- `POST /api/format` -> `format_file`

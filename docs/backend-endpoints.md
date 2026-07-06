# Backend endpoint documentation

This document describes the backend endpoint surface consumed by the CLI
frontend today and intended for future GUI integration.

## Overview

Backend implementation class: `mdnotes_formatter.backend.endpoints.MarkdownFormatterBackend`

The backend currently uses `local-call` invocation style (Python method calls),
but endpoint naming/contracts are intentionally stable to support future
transport adapters (HTTP/RPC/desktop bridge).

## Endpoint: `health`

- **Method type:** `local-call`
- **Handler:** `endpoint_health()`
- **Request body:** none
- **Response:** `dict[str, str]`

### Response shape

```json
{
  "status": "ok",
  "service": "mdnotes-formatter-backend"
}
```

## Endpoint: `list_endpoints`

- **Method type:** `local-call`
- **Handler:** `endpoint_list_endpoints()`
- **Request body:** none
- **Response:** `list[EndpointInfo]`

### `EndpointInfo` fields

- `name` (`str`): stable endpoint identifier.
- `method` (`str`): invocation style (`local-call`).
- `summary` (`str`): human-readable endpoint description.
- `request_type` (`str`): request contract type name.
- `response_type` (`str`): response contract type name.

## Endpoint: `format_file`

- **Method type:** `local-call`
- **Handler:** `endpoint_format_file(request: FormatFileRequest)`
- **Request type:** `FormatFileRequest`
- **Response type:** `FormatFileResponse`

### Request contract: `FormatFileRequest`

```json
{
  "path": "/absolute/or/relative/path/to/note.md"
}
```

### Response contract: `FormatFileResponse`

```json
{
  "original_path": "/path/to/original-note.md",
  "updated_path": "/path/to/Updated-note.md",
  "backup_path": "/path/to/original-note.md.bak",
  "renamed": true
}
```

### Side effects

- Rewrites markdown content in place using formatting requirements.
- Creates `<original>.bak` backup from pre-format content.
- May rename file based on filename normalization rules.

### Error behavior

- Raises `ValueError` when `path` does not end with `.md`.
- Raises `FileNotFoundError` when target file does not exist.

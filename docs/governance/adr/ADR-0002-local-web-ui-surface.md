# ADR-0002: Add Local HTTP Web UI for Search Interaction

## Status
Accepted

## Context
Synexis currently exposes interaction only through CLI commands. Users requested a browser interface to:
- run search queries
- request synthesis summaries
- browse indexed documents and view Markdown/text content

Adding a web entry point introduces a new network-facing surface and untrusted HTTP input handling.

## Decision
Implement a local web UI served by the existing Python runtime using `ThreadingHTTPServer` and `BaseHTTPRequestHandler` in `src/searchctl/web.py`.

Constraints adopted:
- Default bind host is local-only (`127.0.0.1` / `localhost` / `::1`).
- Non-local host binding is denied unless explicitly enabled with `--allow-remote`.
- API stays additive and scoped to local interaction endpoints:
  - `GET /` UI page
  - `GET /api/documents`
  - `GET /api/documents/<doc_id>`
  - `POST /api/search`
- Search/ranking logic is reused unchanged from current retrieval behavior.
- No new third-party web framework dependency is introduced.

## Consequences
Positive:
- Users can interact from browser without changing indexing/retrieval contracts.
- Dependency footprint and supply-chain risk stay stable.
- Exposure defaults are conservative (localhost only).

Negative:
- API contract is implicit in code and currently not versioned as a public external API.
- `POST /api/search` still allows expensive queries and can consume local resources.

## Alternatives Considered
1. Add FastAPI/Flask.
- Rejected for this iteration to avoid dependency expansion and larger blast radius.

2. Keep CLI-only.
- Rejected because it does not satisfy the requested browser interaction capability.

## Migration Plan
No storage schema, chunk identity, scoring contract, or config contract migration is required.

## Rollback Plan
Rollback is code-only:
- remove `searchctl web` command registration in `src/searchctl/cli.py`
- remove `src/searchctl/web.py`
- remove associated tests/docs

No persisted data migration rollback is needed.

## Invariants Impacted
Preserved:
- DOT/pipeline execution model
- chunk identity determinism
- storage schemas (SQLite/OpenSearch/Qdrant)
- scoring and retrieval formula
- additive CLI contract behavior

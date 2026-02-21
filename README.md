# Personal Search (NLSpec v1)

Local-first personal search engine using OpenSearch (BM25), Qdrant (vectors), and SQLite metadata.

## Quickstart

1. Start local backends:
```bash
docker compose up -d
```

2. Create virtualenv and install:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

If you install with `--no-build-isolation`, ensure backend tools are present first:
```bash
pip install -U pip setuptools wheel
pip install -e . --no-build-isolation
```

3. Create config:
```bash
cp config.yaml.example config.yaml
# edit roots in config.yaml
```

4. Ingest documents:
```bash
searchctl ingest --config config.yaml
```

5. Search:
```bash
searchctl search "your query" --config config.yaml
searchctl search "your query" --config config.yaml --json
searchctl search "your query" --config config.yaml --summarize
```

6. Web UI (local interface):
```bash
searchctl web --config config.yaml --host 127.0.0.1 --port 8080
```
Then open `http://127.0.0.1:8080`.
Web serving is powered by FastAPI + Uvicorn.

## Config Setup

- Default config path: `./config.yaml`
- Override via `--config <path>` on every command.
- Required roots are configured under `roots:` and scanned recursively.
- Supported extensions in v1: `.md`, `.pdf`, `.txt`.

## CLI Commands

```bash
searchctl ingest [--config <path>] [--force]
searchctl search "<query>" [--json] [--top N] [--collapse-by-doc] [--source-type <t>] [--path-contains <s>] [--summarize] [--summary-top-k N]
searchctl status [--json]
searchctl inspect --doc "<path>" | --chunk "<chunk_id>" [--json]
searchctl web [--config <path>] [--host 127.0.0.1] [--port 8080] [--allow-remote]
```

`searchctl web` starts a browser-oriented UI with:
- query search and ranked citations
- optional synthesis via OpenRouter (rendered Markdown in left panel)
- indexed document listing and content reading
- rendered Markdown view (headings/lists/code/inline styles), with safe escaping of raw HTML

Security default: non-local bind hosts are rejected unless `--allow-remote` is set.
Runtime default: web search uses BM25-only by default; enable hybrid from the UI checkbox `hybride` (or start server with `--use-hybrid-default`).

## OpenRouter Summary

Configure OpenRouter in `config.yaml`:

```yaml
llm:
  provider: "openrouter"
  base_url: "https://openrouter.ai/api/v1"
  model: "openrouter/auto"
  api_key: "" # optional if OPENROUTER_API_KEY is set
```

Run:

```bash
export OPENROUTER_API_KEY="your-key"
searchctl search "positionnement freelance" --config config.yaml --summarize
```

`--summarize` prints a human-readable synthesis followed by a `Sources` section.
By default summarize mode uses BM25-only retrieval to avoid heavy embedding runtime crashes; add `--summary-use-hybrid` to include vector retrieval.

## Troubleshooting

- Backends not ready:
  - Ensure `docker compose ps` shows `opensearch` and `qdrant` running.
  - Retry `searchctl ingest`; startup readiness checks include bounded retries.

- PDF empty extraction (`PDF_TEXT_EMPTY`):
  - Some PDFs have no extractable text layer.
  - The file is marked as error; ingestion continues.

- Model download/runtime issues:
  - First embedding run downloads the sentence-transformers model.
  - Use CPU by setting `embeddings.device: cpu` in config when needed.
  - If ingest crashes in embedding runtime, run BM25-only ingest:
  - `searchctl ingest --config config.yaml --no-vector`

- Editable install fails with `ModuleNotFoundError: No module named 'setuptools'`:
  - Install build backend dependencies in the active venv:
  - `pip install -U setuptools wheel`
  - Re-run: `pip install -e . --no-build-isolation`

# NLSpec: Local Personal Search Engine (Opinionated v1)

**Stack-locked:** OpenSearch (BM25) + Qdrant (Vectors) + SQLite (Metadata) + Python (CLI) + Sentence-Transformers (Embeddings)

## 0. Status

- **Type:** Normative specification (authoritative)
- **Implementation agent:** Codex
- **Target OS:** Windows + Linux (local-first)
- **Timezone:** Europe/Paris (only relevant for logging timestamps)

---

## 1. Goals (v1)

1. Index personal knowledge sources (Obsidian vault + local docs) into:
   - **Keyword index** (BM25) for exact matching
   - **Vector index** (embeddings) for semantic matching
2. Provide **hybrid search** with:
   - BM25 top-K
   - Vector top-K
   - **RRF fusion**
   - Optional reranking (OFF by default)
3. Provide **exact citations**:
   - file path
   - chunk id
   - char offsets within extracted full text
4. Provide an operational CLI:
   - ingest
   - search
   - status
   - inspect

---

## 2. Out of Scope (v1)

- Emails, Slack, Drive, web crawling
- OCR (images), audio transcription
- Multi-user auth, cloud deployment
- Obsidian plugin UI (CLI only in v1)

---

## 3. Locked Technology Choices (MUST)

### 3.1 Programming language

- Python 3.11+ (MUST)

### 3.2 Search backends

- **OpenSearch 2.x** (MUST) for BM25 indexing/search
- **Qdrant 1.x** (MUST) for vector indexing/search

### 3.3 Metadata store

- **SQLite** (MUST) for document/chunk state, hashes, errors, schema version

### 3.4 Embeddings

- **Sentence-Transformers** (MUST)
- Default model: **`intfloat/e5-small-v2`** (MUST default)
- Embeddings must be normalized (L2) before inserting into Qdrant (MUST)

### 3.5 PDF extraction

- Primary: **PyMuPDF** (`pymupdf`) (MUST)
- Fallback: `pdfminer.six` (SHOULD) only if PyMuPDF fails

### 3.6 Markdown parsing

- Use raw markdown text as searchable content (MUST)
- Extract first H1 as title if present (MUST)

### 3.7 Packaging/runtime

- Provide `docker-compose.yml` to run OpenSearch + Qdrant locally (MUST)
- Provide a Python CLI entrypoint `searchctl` (MUST)

---

## 4. Repository / Project Layout (MUST)

```text
personal-search/
├── README.md
├── config.yaml.example
├── docker-compose.yml
├── pyproject.toml
├── src/
│   └── searchctl/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── logging.py
│       ├── fs_scanner.py
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── markdown.py
│       │   ├── pdf.py
│       │   └── text.py
│       ├── chunking.py
│       ├── hashing.py
│       ├── metadata/
│       │   ├── __init__.py
│       │   ├── db.py
│       │   └── schema.sql
│       ├── opensearch/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── index.py
│       │   └── queries.py
│       ├── qdrant/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── collections.py
│       │   └── queries.py
│       ├── embeddings.py
│       ├── fusion.py
│       ├── snippets.py
│       └── inspect.py
└── tests/
    ├── test_chunking_offsets.py
    ├── test_rrf_fusion.py
    ├── test_incremental_hashing.py
    └── test_e2e_ingest_search.py
```

---

## 5. Configuration (MUST)

### 5.1 Config file location

- Default: `./config.yaml`
- CLI option: `--config <path>`

### 5.2 Config schema (MUST)

```yaml
roots:
  - "C:/path/to/obsidian_vault"
  - "C:/path/to/docs"

include_extensions: [".md", ".pdf", ".txt"]

exclude_globs:
  - "**/.git/**"
  - "**/node_modules/**"
  - "**/.obsidian/**"
  - "**/.trash/**"
  - "**/.DS_Store"
  - "**/Thumbs.db"

chunking:
  target_chars: 2200
  overlap_chars: 250
  min_chunk_chars: 400

embeddings:
  model_name: "intfloat/e5-small-v2"
  batch_size: 32
  device: "auto" # auto|cpu|cuda

opensearch:
  url: "http://localhost:9200"
  index_name: "personal_chunks_v1"

qdrant:
  url: "http://localhost:6333"
  collection_name: "personal_chunks_v1"
  vector_size: 384 # MUST match e5-small-v2 output
  distance: "Cosine" # MUST

indexing:
  reindex_policy: "incremental" # incremental|force
  max_workers: 8

search:
  bm25_top_k: 50
  vector_top_k: 50
  fusion: "rrf"
  rrf_k: 60
  rerank: "off" # off only in v1 (locked)
  rerank_top_k: 20
  return_top_n: 10
  collapse_by_doc_default: false

metadata:
  sqlite_path: "./data/metadata.db"
  extracted_text_cache_dir: "./data/extracted_text"
```

### 5.3 Config constraints (MUST)

- `chunking.overlap_chars < chunking.target_chars`
- `chunking.min_chunk_chars <= chunking.target_chars`
- `qdrant.vector_size` MUST equal the embedding model output dimension
- `qdrant.distance` MUST be `Cosine`

---

## 6. Data Model (Normative)

### 6.1 Document identity (MUST)

Normalize paths:

- Windows: case-insensitive normalization (lowercase drive + path)
- Replace `\` with `/` for internal IDs

```text
doc_id = sha256("path:" + normalized_abs_path)
```

### 6.2 Extracted text hashing (MUST)

```text
content_hash = sha256(extracted_text_utf8)
```

Incremental indexing MUST rely on `content_hash` (not file byte hash).

### 6.3 SQLite schema (MUST)

#### 6.3.1 Tables

```sql
meta(
  schema_version INTEGER NOT NULL
)

documents(
  doc_id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  source_type TEXT NOT NULL, -- markdown|pdf|text
  title TEXT NOT NULL,
  mtime INTEGER NOT NULL, -- unix epoch seconds
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL, -- indexed|partial|error
  error TEXT,
  updated_at INTEGER NOT NULL
)

chunks(
  chunk_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  text_hash TEXT NOT NULL,
  start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL,
  heading_path TEXT,
  FOREIGN KEY(doc_id) REFERENCES documents(doc_id),
  UNIQUE(doc_id, ordinal)
)

errors(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stage TEXT NOT NULL, -- scan|extract|chunk|embed|opensearch|qdrant
  path TEXT,
  doc_id TEXT,
  chunk_id TEXT,
  message TEXT NOT NULL,
  created_at INTEGER NOT NULL
)
```

#### 6.3.2 Schema versioning (MUST)

- `meta.schema_version` MUST start at `1`
- On startup, if schema version mismatch and no migration exists: fail with explicit message

### 6.4 Chunk identity (MUST)

```text
chunk_text_hash = sha256(chunk_text_utf8)
chunk_id = sha256(doc_id + ":" + ordinal + ":" + chunk_text_hash)
```

### 6.5 Chunk payload fields (MUST)

Each chunk MUST include:

- `chunk_id`, `doc_id`, `path`, `title`, `ordinal`
- `text`
- `start_char`, `end_char`
- `heading_path` (nullable)
- `mtime` (from document)

---

## 7. Index Definitions (Normative)

### 7.1 OpenSearch index mapping (MUST)

Index name: `opensearch.index_name` (default `personal_chunks_v1`).

Fields (MUST):

- `chunk_id` (keyword)
- `doc_id` (keyword)
- `path` (keyword + text subfield)
- `title` (text)
- `text` (text)
- `ordinal` (integer)
- `start_char` (integer)
- `end_char` (integer)
- `heading_path` (text or keyword)
- `mtime` (date or long)

BM25:

- Use OpenSearch default BM25 settings (MUST)

Analyzer:

- Standard analyzer is acceptable (MUST)

### 7.2 Qdrant collection (MUST)

Collection name: `qdrant.collection_name` (default `personal_chunks_v1`).

Vectors:

- `size = qdrant.vector_size` (MUST)
- `distance = Cosine` (MUST)

Payload MUST include:

- `chunk_id`, `doc_id`, `path`, `title`, `ordinal`, `start_char`, `end_char`, `heading_path`, `mtime`

---

## 8. Ingestion Pipeline (Normative)

### 8.1 Discovery (MUST)

- Enumerate all files under `roots` recursively
- Include only files with extension in `include_extensions`
- Exclude any file matching `exclude_globs`

### 8.2 Extraction (MUST)

Markdown:

- Extracted text = file content as UTF-8 (with replacement errors)
- Title = first H1 line `^#\s+(.+)$` if present, else filename stem

Text:

- Read as UTF-8 with `errors="replace"` (MUST)

PDF:

- Use PyMuPDF to extract text page by page (MUST)
- If extracted text length < 50 chars: treat as error `PDF_TEXT_EMPTY` (MUST)

### 8.3 Extracted text cache (MUST)

Write extracted full text to:

```text
{extracted_text_cache_dir}/{doc_id}.txt
```

Cache file must be overwritten on doc change.

### 8.4 Chunking (MUST)

- Inputs: extracted full text buffer
- Create chunks targeting `chunking.target_chars`
- Overlap `chunking.overlap_chars`
- Drop chunks `< min_chunk_chars` unless single-chunk doc
- Offsets MUST be valid within extracted full text and align to chunk boundaries:

```text
0 <= start_char < end_char <= len(full_text)
```

### 8.5 Incremental logic (MUST)

For each discovered document:

1. Compute `doc_id`, extract text, compute `content_hash`
2. If `reindex_policy = incremental` and `documents.content_hash == new_content_hash`: SKIP (MUST)
3. If indexing proceeds:
   - Delete previous chunks for doc from OpenSearch and Qdrant (MUST)
   - Delete rows in SQLite `chunks` for doc (MUST)
   - Insert updated `documents` row (UPSERT) (MUST)
   - Chunk, then index each chunk in OpenSearch (MUST)
   - Compute embeddings, then upsert to Qdrant (MUST)
   - Insert chunk rows into SQLite (MUST)

If embedding fails for some chunks:

- Those chunks MUST still be in OpenSearch
- Document status MUST be `partial`
- Errors recorded in `errors` table (MUST)

### 8.6 Concurrency (MUST)

- `max_workers` controls concurrent document processing
- Embedding batches MUST not exceed `batch_size`

---

## 9. Search Pipeline (Normative)

### 9.1 Query handling (MUST)

- Query is a string
- For vector search:
  - embed query using same model (MUST)
  - normalize embedding (L2) (MUST)

### 9.2 Retrieval (MUST)

- Run BM25 query in OpenSearch: return top `bm25_top_k`
- Run vector search in Qdrant: return top `vector_top_k`
- Fuse via Reciprocal Rank Fusion (RRF) (MUST):

```text
rrf_score = sum(1 / (rrf_k + rank_source))
```

- Rank sources are 1-based (MUST)
- Sort by fused score descending; tie-break by:
  - lowest (best) BM25 rank
  - lowest vector rank
  - lexicographic `chunk_id` (MUST deterministic)

### 9.3 Result shaping (MUST)

For each result (top `return_top_n`), produce:

- `rank`, `score`
- `doc_path`, `doc_title`
- `snippet`
- `citation: {chunk_id, start_char, end_char}`
- `signals: {bm25_rank?, vector_rank?, fusion_method:"rrf"}`

### 9.4 Snippet (MUST)

- If BM25 hit includes match highlights: center snippet around the first highlight (best-effort)
- Else: `snippet = first 240 characters of chunk text`
- Snippet length MUST be between 120 and 360 chars when possible

### 9.5 Optional collapse (MUST)

CLI flag `--collapse-by-doc`:

- If enabled, keep only best-ranked chunk per `doc_id`

---

## 10. CLI (MUST)

### 10.1 Entry point

- `searchctl` (console script)

### 10.2 Commands (MUST)

```bash
searchctl ingest [--config <path>] [--force]
searchctl search "<query>" [--json] [--top N] [--collapse-by-doc] [--source-type <t>] [--path-contains <s>]
searchctl status [--json]
searchctl inspect --doc "<path>" | --chunk "<chunk_id>" [--json]
```

- `--force` sets `reindex_policy=force` for this run

### 10.3 CLI output (MUST)

- Default: human readable
- `--json`: machine output matching the data model in section 9.3

---

## 11. Docker Compose (MUST)

### 11.1 Services (MUST)

- OpenSearch single-node (dev) exposed on `9200`
- Qdrant exposed on `6333`
- Persist volumes in `./data/` (MUST)

### 11.2 Deterministic startup

- `searchctl ingest` MUST detect backend readiness (retry with bounded backoff)

---

## 12. Logging & Diagnostics (MUST)

### 12.1 Logging rules

- Log levels: `ERROR` / `WARN` / `INFO` / `DEBUG`
- Default: `INFO`
- MUST NOT log chunk text at `INFO`/`WARN`/`ERROR`
- `DEBUG` may log first 80 chars of chunk only if `--debug` flag enabled

### 12.2 Status command content

- `docs_total`, `docs_indexed`, `docs_partial`, `docs_error`
- `chunks_total`
- `last_ingest_timestamp`
- backend connectivity status (`opensearch`/`qdrant`)

---

## 13. Acceptance Criteria (MUST)

### 13.1 Incremental correctness

Given a corpus, run ingest twice:

- second run MUST perform zero deletions and zero reindex operations (except connectivity checks)

Modify one markdown file content:

- next ingest MUST reindex only that doc's chunks

### 13.2 Hybrid quality

- Keyword query with exact term MUST return matching doc in top 5
- Paraphrased query with no shared keywords MUST still return relevant doc in top 10 (semantic path)

### 13.3 Citations validity

- Returned `start_char`/`end_char` MUST correspond to a substring of the cached extracted text file `{doc_id}.txt`
- `inspect --chunk <id>` MUST display that substring boundaries

### 13.4 Resilience

- A corrupted PDF MUST be recorded as error and ingestion continues
- `status` MUST show the error count

### 13.5 Portability

- Works with paths containing spaces and accented characters on Windows

---

## 14. Test Suite Requirements (MUST)

### 14.1 Unit tests

- Chunker offsets valid and stable
- RRF fusion math correctness + deterministic ordering
- Incremental hashing correctness (content-hash based)

### 14.2 Integration test (E2E)

Create fixture corpus:

- 2 markdown notes
- 1 txt
- 1 small PDF

Then:

- run ingest
- run search (keyword + paraphrase) and assert non-empty results
- validate `--json` schema keys exist

---

## 15. Definition of Done (MUST)

- All acceptance criteria pass
- Tests pass locally
- `README` includes:
  - quickstart (`docker-compose up`, `pip install`, ingest, search)
  - config setup
  - troubleshooting (backends not ready, PDF empty, model download)

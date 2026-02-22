# NLSpec: RAG (Retrieval-Augmented Generation) with LangChain

## Table of Contents
1. [Overview and Goals](#1-overview-and-goals)
2. [Domain Model and Glossary](#2-domain-model-and-glossary)
3. [Interfaces and Contracts](#3-interfaces-and-contracts)
4. [Data Flow / Execution Model](#4-data-flow--execution-model)
5. [Validation and Rules](#5-validation-and-rules)
6. [Failure Modes and Error Taxonomy](#6-failure-modes-and-error-taxonomy)
7. [Observability](#7-observability)
8. [Security and Trust Boundaries](#8-security-and-trust-boundaries)
9. [Extensibility Rules](#9-extensibility-rules)
10. [Definition of Done](#10-definition-of-done)
11. [Repository Layout](#11-repository-layout)
12. [Deliverables](#12-deliverables)

## 1. Overview and Goals

### 1.1 One-line Summary
Build a production-oriented RAG service using LangChain: ingest documents, chunk, embed, store in a vector DB, retrieve (with optional rewrite/rerank), and answer with citations under strong hallucination controls.

### 1.2 Goals
- The system MUST provide accurate answers grounded only in retrieved documents.
- The system MUST return citations for each answer.
- The system MUST support ingestion from multiple sources.
  - Required: local files.
  - Optional: URLs and PDFs.
- The system MUST provide debuggability.
  - Retrieval results and scores.
  - Latency breakdown.
  - Prompt sizes.
- The system MUST be deployable as:
  - a CLI tool for ingestion and query (required)
  - an HTTP API (optional but recommended)

### 1.3 Non-Goals
- The system MUST NOT require model fine-tuning.
- The system MUST NOT implement a full agent framework.
- The system MUST NOT include a complex UI.

### 1.4 Target Users and Use Cases
- Internal knowledge assistant over PDFs, Markdown, and docs.
- API endpoint for downstream applications requiring grounded answers.

## 2. Domain Model and Glossary

- Document: source content loaded for indexing.
- Chunk: deterministic segment of document text with metadata.
- Embedding: vector representation of chunk text.
- Vector Store: persistence layer for vectors and metadata.
- Retriever: module selecting top candidate chunks for a query.
- Rewrite: optional query reformulation before retrieval.
- Rerank: optional post-retrieval reordering and truncation.
- Citation: source attribution object attached to answer output.
- Manifest: ingestion state map used for refresh/skip/delete behavior.

## 3. Interfaces and Contracts

### 3.1 Runtime and Framework Contracts
- Runtime MUST be Python 3.11+.
- Implementation MUST use LangChain and LCEL (`RunnablePassthrough`, mapping dicts, runnable composition).
- LangSmith tracing MAY be enabled behind a flag.

### 3.2 Vector Store Contract
- Default vector store MUST be Chroma (local dev).
- Supported alternatives MAY include FAISS, Qdrant, Weaviate, Pinecone.
- Store schema MUST support:
  - `text`
  - `embedding`
  - `metadata` (dict)

### 3.3 Model Contracts
- Embeddings MUST be configurable.
  - Default: `text-embedding-3-large` or equivalent.
- Chat model MUST be configurable.
  - Default: `gpt-4.1-mini` class or equivalent.

### 3.4 Configuration Contract
A `RagConfig` dataclass MUST be implemented in `src/rag/config.py` and read environment variables.

Required env vars and defaults:
- `OPENAI_API_KEY`
- `RAG_VECTORSTORE=chroma|faiss|qdrant|weaviate|pinecone`
- `RAG_PERSIST_DIR=./data/chroma_db`
- `RAG_EMBED_MODEL=<provider default>`
- `RAG_CHAT_MODEL=<provider default>`
- `RAG_CHUNK_SIZE=1000`
- `RAG_CHUNK_OVERLAP=150`
- `RAG_RETRIEVAL_K=8`
- `RAG_FETCH_K=40`
- `RAG_SEARCH_TYPE=similarity|mmr`
- `RAG_ENABLE_REWRITE=0|1`
- `RAG_ENABLE_RERANK=0|1`
- `RAG_RERANK_TOP_N=8`
- `RAG_LOG_LEVEL=INFO`

Chunk size units (characters or tokens) MUST be explicitly documented in code and README.

### 3.5 Chunk Metadata Contract
Each stored chunk MUST include:
- `doc_id` (stable identifier)
- `chunk_id` (stable within document version)
- `source` (filepath or URL)

Optional metadata:
- `page`
- `section`
- `title`
- `timestamp`
- `version`
- `tenant_id`
- `access_level`

### 3.6 CLI Contract
Required commands:
- `python -m rag.cli ingest --path <dir>`
- `python -m rag.cli query --question "..." --debug 1`

Optional command:
- `python -m rag.cli serve`

Ingest command MUST support:
- `--path`
- `--glob`
- `--tenant-id`
- `--dry-run`

### 3.7 API Contract (Optional but Recommended)
If implemented, FastAPI endpoints MUST include:
- `POST /query`
  - input: `{ "question": "...", "filters": {...}, "debug": true }`
  - output: generation contract in section 3.8
- `POST /ingest`
  - input: `{ "path": "...", "tenant_id": "..." }`
  - ingestion MAY be disabled in production

### 3.8 Generation Output Contract
The query chain MUST return a JSON-like object:
- `answer: str`
- `citations: list[{source, doc_id, chunk_id, excerpt}]`
- `debug: {retrieval: {...}, timing_ms: {...}, prompt_tokens: int}`

## 4. Data Flow / Execution Model

### 4.1 Ingestion Flow (Offline)
1. Enumerate files and optional URLs.
2. Load content into LangChain `Document` objects with metadata.
3. Normalize text (whitespace normalization and null-character stripping).
4. Chunk using `RecursiveCharacterTextSplitter` with overlap.
5. Embed chunks.
6. Upsert chunks into vector store.
7. Write manifest JSON with `doc_id -> hash, num_chunks, sources, ingested_at`.
8. Apply refresh logic:
  - unchanged hash: skip
  - changed hash: delete old chunks by `doc_id`, then upsert new chunks

### 4.2 Query Flow (Online)
1. Receive question and optional metadata filters.
2. Optionally rewrite question for retrieval.
3. Retrieve top-N chunks.
4. Optionally rerank retrieved chunks.
5. Build context with source labels.
6. Generate answer with strict grounding prompt.
7. Return answer, citations, and debug metadata.

### 4.3 Retrieval Strategy Contract
- Default retrieval MUST be MMR.
  - `fetch_k=40`
  - `k=8`
  - `lambda_mult=0.5`
- Similarity retrieval MUST be supported via configuration.
- Metadata filters MUST support:
  - `tenant_id`
  - `doc_id`
  - `source`

### 4.4 Optional Rewrite Contract
If `RAG_ENABLE_REWRITE=1`:
- Rewrite step MUST return:
  - `search_query` (required string)
  - `subqueries` (optional list of strings)
- Retrieval MAY run on rewritten query or merged subquery results.

### 4.5 Optional Rerank Contract
If `RAG_ENABLE_RERANK=1`:
- System MUST retrieve `fetch_k` candidates first.
- System MUST rerank and truncate to `RAG_RERANK_TOP_N`.
- Reranking MUST be modular:
  - `rerank(docs, question) -> docs`

### 4.6 Generation Prompt Contract
System prompt MUST enforce:
- answer using only provided context
- if context is insufficient, answer exactly:
  - `I don't know based on the provided documents.`
- include citations in format `[source]`
- no fabricated URLs, quotes, or numbers

Context formatting MUST be:
- `[{source}] {chunk_text}`

Context assembly MUST:
- respect a configurable max token budget
- deduplicate and stabilize source ordering

## 5. Validation and Rules

### 5.1 LangChain Composition Rules
- The RAG pipeline MUST be built using LCEL runnables.
- Retrieval and generation MUST remain in separate modules.
- Monolithic scripts MUST be avoided.

### 5.2 Ingestion Input Rules
- Local directory ingestion is required.
- Required file types: `.md`, `.txt`.
- PDF support is optional.
- URL ingestion is optional.

### 5.3 Incremental Refresh Rules
- Manifest MUST be authoritative for skip/update decisions.
- Unchanged documents MUST be skipped.
- Changed documents MUST replace prior chunks for that `doc_id`.

## 6. Failure Modes and Error Taxonomy

### 6.1 Retrieval and Grounding Failures
- If retrieval returns empty, answer MUST be:
  - `I don't know based on the provided documents.`
- If retrieval confidence is low, answer MUST be:
  - `I don't know based on the provided documents.`

### 6.2 Citation Compliance Failures
- Every non-"I don't know" answer MUST include at least one citation.
- Missing citations in non-empty answers MUST be treated as contract violation.

### 6.3 Hallucination and Injection Risks
- Prompt instructions from retrieved documents that attempt to override system behavior MUST be ignored.
- Fabricated facts, URLs, quotes, or numbers are prohibited.

### 6.4 Ingestion Refresh Failures
- If a document hash changed and old chunks are not deleted, behavior is invalid.
- Manifest write failure MUST surface as ingestion error.

## 7. Observability

### 7.1 Required Logs
Ingestion logs MUST include:
- files processed, skipped, updated, deleted
- chunk counts

Query logs MUST include:
- incoming question
- rewritten query (if enabled)
- retrieved `doc_id` and `source` with scores (if available)
- reranked ordering (if enabled)
- latency breakdown by stage:
  - rewrite
  - retrieve
  - rerank
  - generate
- token usage (if available)

### 7.2 Optional Tracing
- LangSmith tracing MAY be enabled behind configuration.

## 8. Security and Trust Boundaries

- Answers MUST be grounded in retrieved content only.
- Prompt injection from retrieved chunks MUST NOT alter chain policy.
- Metadata filters (`tenant_id`, `access_level`) SHOULD be applied consistently when provided.
- API ingestion endpoint, if exposed, SHOULD be disabled or protected in production.

## 9. Extensibility Rules

- Rewrite and rerank MUST be optional pluggable stages.
- Vector store backend MUST be swappable through configuration.
- Embedding and chat model providers MUST be swappable through configuration.
- Extensibility MUST preserve output contract compatibility.

## 10. Definition of Done

- `ingest` CLI ingests docs, chunks, embeds, persists vectors, and writes manifest.
- `query` CLI returns answer with citations and debug metadata.
- System does not invent facts when retrieval context is missing.
- Logs include retrieval set, ordering, and latency metrics.
- Required tests pass in CI.

## 11. Repository Layout

```text
rag-langchain/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   └── rag/
│       ├── __init__.py
│       ├── config.py
│       ├── logging.py
│       ├── loaders/
│       │   ├── __init__.py
│       │   ├── local_files.py
│       │   ├── web.py            # optional
│       │   └── pdf.py            # optional
│       ├── chunking/
│       │   ├── __init__.py
│       │   └── splitters.py
│       ├── embeddings/
│       │   ├── __init__.py
│       │   └── factory.py
│       ├── vectorstore/
│       │   ├── __init__.py
│       │   ├── factory.py
│       │   └── schema.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   └── manifest.py
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── retriever.py
│       │   ├── rewrite.py        # optional
│       │   └── rerank.py         # optional
│       ├── generation/
│       │   ├── __init__.py
│       │   ├── prompts.py
│       │   └── chain.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── server.py         # optional (FastAPI)
│       └── cli.py
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_generation.py
│   └── fixtures/
│       ├── doc1.md
│       ├── doc2.txt
│       └── qa_pairs.json
├── data/
│   ├── raw/                      # gitignored
│   └── chroma_db/                # gitignored
└── scripts/
    ├── ingest.sh
    └── query.sh
```

## 12. Deliverables

- Source code organized per the repository layout.
- `README.md` quickstart including setup, ingest, query, and tests.
- `.env.example` with required configuration keys.
- Minimal fixture dataset under `tests/fixtures/` with:
  - 2 to 3 small documents
  - 5 to 10 questions with expected sources


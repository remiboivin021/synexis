# STATE — RAG LangChain Service

Branch: feature/rag-langchain
Worktree: /home/comeg/workspace/synexis_brain/wt-rag-langchain
Planner: codex
Executor: codex

---

# Mission

Implement the `rag.nlspec.md` contract as a new `rag` package that coexists with existing `searchctl` code, with minimal blast radius and no feature deletion.

---

# Feature Type

- [x] new feature
- [ ] bug fix
- [ ] refactor (approved)
- [ ] performance improvement
- [ ] infrastructure
- [ ] security

---

# Acceptance Criteria

- [ ] `python -m rag.cli ingest --path <dir>` ingests `.md` and `.txt` files, chunks, embeds, persists to vectorstore, and writes a manifest.
- [ ] `python -m rag.cli query --question "..." --debug 1` returns grounded answers with citations and debug metadata.
- [ ] Empty retrieval forces exact fallback answer: `I don't know based on the provided documents.`
- [ ] RAG modules are separated (`ingestion`, `retrieval`, `generation`, config/factories), not monolithic.
- [ ] Required tests for ingestion/retrieval/generation pass locally.
- [ ] Existing `searchctl` behavior remains available.

---

# Scope Contract

## Allowed Areas

- `rag.nlspec.md`
- `.env.example`
- `README.md`
- `pyproject.toml`
- `src/rag/**`
- `tests/test_ingestion.py`
- `tests/test_retrieval.py`
- `tests/test_generation.py`
- `tests/fixtures/**`
- `scripts/ingest.sh`
- `scripts/query.sh`
- `STATE.rag-langchain.md`
- `TODO.rag-langchain.md`
- `DECISIONS.rag-langchain.md`

## Forbidden Areas

- `.agents/` templates and skills
- existing `searchctl` module internals unless strictly required for compatibility
- existing metadata SQL schema for `searchctl`
- unrelated refactors

---

# Blast Radius Assessment

- [ ] localized (single module)
- [x] multi-module
- [ ] cross-system
- [ ] unknown

---

# Architectural Constraints

- Keep existing `searchctl` package untouched unless unavoidable.
- New RAG implementation must be additive under `src/rag`.
- Prefer optional integrations (rewrite/rerank/API) with safe defaults off.
- Preserve deterministic chunk identity and manifest refresh behavior.

---

# Parallel Safety Check

- Work is isolated in `feature/rag-langchain` dedicated worktree.
- No shared schema mutation planned.

---

# Execution Plan (Planner Output)

1. Implement `src/rag` package core contracts (config, loaders, chunking, embeddings, vectorstore, ingestion, retrieval, generation, CLI) with minimal optional stubs.
2. Add deterministic tests and fixtures for ingestion skip logic, retrieval relevance, and generation citation/empty-context behavior.
3. Update packaging/docs/env/scripts to expose and run the new RAG service.

---

# Refactor Shield

No opportunistic changes outside the listed paths.

---

# Security Surface Check

Touches untrusted input ingestion and optional API surface. Keep API optional and disabled by default.

---

# Definition of Done

All acceptance criteria are checked and new targeted tests pass.

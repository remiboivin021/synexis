# STATE — NLSpec Bootstrap

Branch: feature/bootstrap  
Worktree: /home/comeg/workspace/synexis_brain/wt-bootstrap  
Planner: codex  
Executor: codex  

---

# Mission

Implement the Local Personal Search Engine v1 defined in `synexis.nlspec.md` using the locked stack and deliver a runnable CLI with deterministic incremental ingest + hybrid retrieval + citations.

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

- [ ] Repository layout and Python package structure match NLSpec section 4.
- [ ] `searchctl ingest/search/status/inspect` commands exist and run.
- [ ] Incremental indexing uses extracted text `content_hash` and skips unchanged docs.
- [ ] OpenSearch BM25 + Qdrant vector retrieval are fused via deterministic RRF.
- [ ] Search results include citations with `chunk_id/start_char/end_char`.
- [ ] SQLite schema + cache files are created and used as specified.
- [ ] Docker compose runs OpenSearch and Qdrant with persisted `./data` volumes.
- [ ] Required unit and integration tests are implemented.
- [ ] README contains quickstart/config/troubleshooting.

---

# Scope Contract

## Allowed Areas

- README.md
- config.yaml.example
- docker-compose.yml
- pyproject.toml
- src/searchctl/**
- tests/**
- docs/governance/constitution.md
- STATE.bootstrap.md
- TODO.bootstrap.md
- DECISIONS.bootstrap.md

## Forbidden Areas

- `.agents/` templates and skill files
- AGENTS.md policy text
- Any additional architecture/governance rewrites unrelated to this feature

---

# Blast Radius Assessment

- [ ] localized (single module)  
- [ ] multi-module  
- [x] cross-system  
- [ ] unknown  

---

# Architectural Constraints

- Keep one-package CLI architecture defined by NLSpec.
- Preserve deterministic behavior and explicit contracts.
- Do not introduce alternate orchestration beyond CLI + module functions.

---

# Parallel Safety Check

- No other active feature worktrees detected for this repository.

---

# Execution Plan (Planner Output)

1. Bootstrap governance/feature artifacts and core project scaffold (done when preflight passes and base files exist).
2. Implement config, metadata schema, extraction/chunking/hashing, embeddings, OpenSearch/Qdrant clients, fusion, snippets, inspect, and CLI commands (done when package imports cleanly).
3. Add tests, compose, and docs, then run targeted tests and fix failures (done when tests pass locally).
4. Finalize acceptance checklist in TODO/STATE and provide commit evidence.

---

# Refactor Shield

No opportunistic refactor outside the declared package and tests.

---

# Security Surface Check

Touches local backend connectivity and file ingestion only; no auth/secrets surface expansion.

---

# Definition of Done

All acceptance criteria above are checked and tests pass.


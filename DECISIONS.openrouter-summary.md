# DECISIONS — OpenRouter Summary

## Rules
- Log only non-trivial decisions.
- Each decision references one `Task` and one `Commit`.
- Architectural decisions require ADR.

## Decision Log

### [D-001] Use OpenRouter chat completions endpoint with explicit prompt template

Context: Need provider-level integration with deterministic output shape.
Decision: Implement a dedicated OpenRouter client module and prompt builder module.
Rationale: Keeps CLI logic clean and testable while making prompt strategy explicit.
Task: T-001
Commit: 94d5d68
Impact: medium, module
Date: 2026-02-20

### [D-002] Add summary mode in search with guaranteed source list

Context: User needs human-readable synthesis and explicit sources at the end.
Decision: Add `--summarize` to search, generate synthesis via OpenRouter prompt, and append `Sources`.
Rationale: Preserves existing retrieval pipeline while adding understandable output layer.
Task: T-002
Commit: af13bb9
Impact: medium, module
Date: 2026-02-20

### [D-003] Keep summarization opt-in and preserve default search output

Context: Existing search users expect direct ranked results unless explicitly asking for synthesis.
Decision: Add `--summarize` as opt-in mode; no behavior change for default and `--json` modes.
Rationale: Backward compatibility while enabling LLM-based summary workflow.
Task: T-003
Commit: 1bdd5bb
Impact: low, module
Date: 2026-02-20

### [D-004] Default summarize mode to BM25-only to avoid embedding segfaults

Context: User observed process-level segmentation fault when running summarize with embedding runtime load.
Decision: Avoid eager embedding import and disable vector retrieval by default in summarize mode.
Rationale: Keeps summarize path stable; hybrid mode remains available via `--summary-use-hybrid`.
Task: T-004
Commit: e867da8
Impact: medium, module
Date: 2026-02-20

### [D-005] Reintroduce qdrant probe helper expected by CLI

Context: `cli.py` imports `probe_collection_write` but the branch-local qdrant collections module did not define it.
Decision: Add `probe_collection_write` back in `qdrant/collections.py`.
Rationale: Restores import consistency and startup behavior for ingest/readiness checks.
Task: T-005
Commit: 2cd080e
Impact: low, localized
Date: 2026-02-20

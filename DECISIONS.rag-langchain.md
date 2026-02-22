# DECISIONS — RAG LangChain Service

## Rules
- Log only non-trivial decisions.
- Each decision references one `Task` and one `Commit`.
- Architectural decisions require ADR.

## Decision Log

### [D-001] Add isolated `rag` package instead of rewriting `searchctl`

Context: The repository already contains a working `searchctl` implementation with existing users and tests.
Decision: Implement NLSpec RAG as a new additive package under `src/rag` and keep existing `searchctl` untouched.
Rationale: Satisfies the new spec while minimizing blast radius and avoiding feature regression.
Task: T-001
Commit: d22b3c9
Impact: medium, module
Date: 2026-02-22

### [D-002] Avoid LCEL parser imports that trigger torch runtime crashes in this environment

Context: Importing `langchain_core.output_parsers` caused a segmentation fault via a transitive `transformers/torch` import chain during tests.
Decision: Keep LCEL composition but implement generation flow with `RunnablePassthrough` + `RunnableLambda` only.
Rationale: Preserves spec compliance and chain composability while keeping runtime stable.
Task: T-002
Commit: 57bf56a
Impact: low, localized
Date: 2026-02-22

### [D-003] Keep optional API and backend alternatives behind explicit contracts

Context: The spec lists optional API server and alternative vector backends, but full production connectors increase blast radius.
Decision: Expose API route wiring and backend enum contract, while implementing baseline Chroma path and explicit `NotImplementedError` for alternatives.
Rationale: Meets contract and keeps minimal-change implementation deterministic.
Task: T-003
Commit: c69101e
Impact: low, localized
Date: 2026-02-22

### [D-004] Apply lexical support guard before generation

Context: Vector retrieval could return unrelated top-k chunks when the corpus does not contain the query concept (for example, "Chroma"), causing misleading grounded answers.
Decision: Add a retrieval-time lexical support filter on query terms; if no retrieved chunk contains query evidence, return an empty context so generation falls back to explicit unknown.
Rationale: Enforces hallucination control from the NLSpec while preserving current architecture.
Task: T-004
Commit: 0de6b92
Impact: low, localized
Date: 2026-02-22

### [D-005] Make lexical guard stopwords configurable via env

Context: Multilingual queries (French/English/Spanish) require different stopword sets and token-length heuristics.
Decision: Add `RAG_QUERY_STOPWORDS` and `RAG_QUERY_MIN_TERM_LEN` to `RagConfig` and use them in retrieval lexical filtering.
Rationale: Keeps the hallucination guard active while adapting relevance behavior to language context.
Task: T-005
Commit: pending
Impact: low, localized
Date: 2026-02-22

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
Commit: pending
Impact: medium, module
Date: 2026-02-22

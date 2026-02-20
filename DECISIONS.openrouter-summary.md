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
Commit: pending
Impact: medium, module
Date: 2026-02-20

### [D-002] Add summary mode in search with guaranteed source list

Context: User needs human-readable synthesis and explicit sources at the end.
Decision: Add `--summarize` to search, generate synthesis via OpenRouter prompt, and append `Sources`.
Rationale: Preserves existing retrieval pipeline while adding understandable output layer.
Task: T-002
Commit: pending
Impact: medium, module
Date: 2026-02-20

### [D-003] Keep summarization opt-in and preserve default search output

Context: Existing search users expect direct ranked results unless explicitly asking for synthesis.
Decision: Add `--summarize` as opt-in mode; no behavior change for default and `--json` modes.
Rationale: Backward compatibility while enabling LLM-based summary workflow.
Task: T-003
Commit: pending
Impact: low, module
Date: 2026-02-20

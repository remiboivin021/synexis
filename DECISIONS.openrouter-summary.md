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

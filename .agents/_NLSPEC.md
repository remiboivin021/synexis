# <System / Component Name> — Natural Language Specification (NLSpec)

Status: Draft | Accepted | Deprecated  
Owner: <team / role>  
Last Updated: <yyyy-mm-dd>  
Related ADRs: <adr links>

---

# 1. Overview

## 1.1 Purpose
Describe what this system/component is and why it exists.

Focus on:
- the problem it solves
- who depends on it
- why it must be specified formally

## 1.2 Goals
List the outcomes this system MUST guarantee.

Example:
- deterministic pipeline traversal
- stable public contracts
- resumable execution

## 1.3 Non-Goals
Explicitly state what this system will NOT do.

This prevents scope drift.

---

# 2. Authority and Scope

This NLSpec is authoritative for:

- behavior
- contracts
- invariants
- defaults
- validation rules

If implementation diverges from this specification, the specification takes precedence until updated via ADR.

---

# 3. Definitions and Glossary (Minimal)

Define only terms that prevent ambiguity.

Example:

| Term | Meaning |
|------|--------|
| Pipeline | Directed execution graph |
| Handler | Execution unit for a node |
| Outcome | Result of stage execution |

Avoid over-documenting.

---

# 4. System Model

Describe the system at a structural level.

## 4.1 High-Level Architecture
Explain components and responsibilities in full sentences.

Avoid diagrams unless absolutely necessary.

Example structure:

- Orchestrator
- Execution engine
- State store
- Validation layer

## 4.2 Design Principles

Prefer constraints over philosophy.

Examples:

- Deterministic behavior over implicit magic  
- Minimal runtime state  
- Explicit contracts  
- Safe defaults  

---

# 5. Contracts and Interfaces

This section is critical.

## 5.1 Public Contracts

Define every contract that other systems rely on:

- config schema
- API
- CLI
- DSL
- file formats
- status envelopes

### Rules
- Defaults MUST be specified.
- Optional vs required MUST be clear.
- Breaking change policy MUST be stated.

Example:

> Fields must never be renamed silently.  
> Additive evolution is preferred.

---

## 5.2 Internal Contracts

Define boundaries between subsystems.

Focus on:

- data flow
- ownership
- invariants

Example:

> Execution engine MUST NOT mutate pipeline definitions.

---

# 6. Execution / Behavior Model

Describe runtime behavior **deterministically**.

Use pseudocode when helpful.

Include:

- lifecycle
- ordering guarantees
- routing logic
- retries
- state updates

### Required Rule:
Behavior must be predictable from the spec alone.

No “implementation decides”.

---

# 7. Data Model

Define:

- schemas
- identities
- hashing
- versioning
- serialization rules

### MUST clarify:
- what is mutable
- what is append-only
- what is immutable

---

# 8. Invariants (CRITICAL)

List rules that must never drift without ADR.

Examples:

- identity must be deterministic
- orphaned records are forbidden
- contracts must not silently change
- trust boundaries must be explicit

If an invariant changes → ADR required.

---

# 9. Validation and Linting

Define what makes the system **invalid**.

Separate:

## Hard Errors
System must refuse operation.

## Warnings
Allowed but risky.

Example:

Hard error:
> Missing start node.

Warning:
> Retry target not defined.

---

# 10. Failure Model

Enumerate failure classes.

Example:

### Retryable
- transient network errors
- rate limits

### Terminal
- schema violations
- invalid configuration

### Systemic
- invariant violations

Define engine behavior for each.

No ambiguity allowed.

---

# 11. Security and Trust Boundaries

Required whenever the system touches:

- network
- file system
- secrets
- connectors
- subprocesses

Define:

- default posture (recommended: default deny)
- capability model
- isolation rules

Example:

> Connectors are opt-in capabilities and must be explicitly enabled.

---

# 12. Observability

Specify:

- logs
- metrics
- traces
- audit trails

### Hard rules:
- never log secrets  
- avoid high-cardinality metrics  

Define what operators MUST be able to answer:

Example:
> Which stage failed and why?

---

# 13. Performance Expectations (Optional but Recommended)

Define guardrails, not fantasies.

Example:

- pipeline startup < 2s
- checkpoint write < 50ms
- bounded retry backoff

Avoid premature optimization.

---

# 14. Extensibility Rules

Prevent architecture rot.

Define:

- where extension is allowed
- where it is forbidden

Example:

> New node types must register via the handler registry.  
> Core traversal logic must not be modified.

---

# 15. Compatibility and Evolution

Define how the system evolves safely.

### Required:
- additive-first policy
- migration requirement for breaking changes
- rollback expectation

Example:

> Breaking config changes require migration guidance and ADR.

---

# 16. Definition of Done (MANDATORY)

Make this executable.

Use checklists.

Example:

## Parsing
- [ ] accepts valid schema
- [ ] rejects malformed definitions

## Execution
- [ ] deterministic traversal
- [ ] retry policy respected

## Contracts
- [ ] defaults applied correctly

## Failure handling
- [ ] retryable vs terminal respected

## Observability
- [ ] structured logs emitted

A spec without DoD is not complete.

---

# 17. Open Questions (Optional)

List only real blockers.

Avoid speculation.

---

# 18. Out of Scope

Restate exclusions to protect the boundary.

---

# 19. Appendix (Optional)

Use for:

- grammars
- reference tables
- attribute matrices
- status envelopes

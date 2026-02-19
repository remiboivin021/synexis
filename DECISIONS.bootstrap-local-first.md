# DECISIONS — bootstrap-local-first

## Rules
- Log only non-trivial decisions.
- Each decision references one `Task` and one `Commit`.
- Architectural decisions require ADR.

## Decision Log

### [D-001] Scope bootstrap en deux tâches

Context: Repo initial quasi vide; demande globale très large.
Decision: Exécuter une tranche prioritaire (foundations + DOT runner) avec commits atomiques.
Rationale: Maximiser le ROI immédiat sans dérive de scope.
Task: T-001
Commit: pending
Impact: medium, module
Date: 2026-02-19

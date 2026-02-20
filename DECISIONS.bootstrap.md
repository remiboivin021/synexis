# DECISIONS — <feature-name>

## Rules
- Log only non-trivial decisions.
- Each decision references one `Task` and one `Commit`.
- Architectural decisions require ADR.

## Decision Log

### [D-001] Gate backend e2e test behind explicit env flag

Context: OpenSearch/Qdrant availability and model download are environment-dependent in local and CI runs.
Decision: Keep required e2e test implemented, but guard execution behind `RUN_E2E=1`.
Rationale: Preserves deterministic default test pass while still providing full integration validation when services are ready.
Task: T-003
Commit: c56cfad
Impact: low, module
Date: 2026-02-20

### [D-002] Document no-build-isolation backend requirement

Context: `pip install -e . --no-build-isolation` fails if build backend deps are absent in the venv.
Decision: Add troubleshooting and explicit install sequence for `setuptools` and `wheel`.
Rationale: Reduces setup failure for local-first workflows that disable build isolation.
Task: T-004
Commit: 914729a
Impact: low, localized
Date: 2026-02-20

### [D-003] Keep JSON contract and add readable text rendering for search

Context: Default `search` output was raw Python dict/list text and hard to read in terminal usage.
Decision: Add a dedicated human formatter for `search` default mode and keep `--json` unchanged.
Rationale: Improves UX without breaking machine consumers.
Task: T-005
Commit: pending
Impact: low, module
Date: 2026-02-20

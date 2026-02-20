# SKILL OPERATING SYSTEM (GLOBAL)

This section defines the universal operating model for all skills.
It is designed to be reusable across repositories.

All skills MUST follow these rules.

Canonical governance reference:
`docs/governance/constitution.md`

---

# Prime Directive

If unsure which skill to use → ALWAYS invoke `$governance`, then `$triage`.

Never guess.
Never improvise structure.

---

# Core Principles

## 1. Single Writer Rule
Only `$coder` is allowed to modify production code.

All other skills are read-only:
- they analyze
- they gate
- they propose
- they veto

They NEVER implement.

---

## 2. Authority Over Execution
Authority defines who can BLOCK a change — not who writes code.

Execution belongs exclusively to `$coder`.

---

## 3. Minimal Change Philosophy
Skills MUST prefer the smallest possible safe change.

Avoid:
- opportunistic refactoring  
- unrelated improvements  
- stylistic rewrites  

Local optimization > global rewrites.

---

## 4. Determinism Over Creativity
Skills must favor predictable behavior over clever solutions.

Prefer:
- existing patterns  
- established modules  
- known architecture  

Never introduce new patterns without approval from `$architect`.

---

## 5. Explicit Escalation
When risk or uncertainty appears:

STOP → escalate.

Never continue with assumptions.

---

# Global Routing Rule

If unsure which skill to use → ALWAYS invoke `$governance`, then `$triage`.

# Skill Routing Map

Use this deterministic routing:

- constitutional/invariant/governance checks → invoke `$governance`
- incoming request classification / flow selection → invoke `$triage`
- unclear scope / planning needed → invoke `$planner`
- execution readiness gate before coding → invoke `$preflight`
- implementation / code changes → invoke `$coder`
- structural direction / boundaries / patterns → invoke `$architect`
- architectural + security-sensitive change (combined risk) → invoke `$architect-security`
- security-sensitive surfaces → invoke `$security`
- behavioral validation / tests / regressions → invoke `$qa`
- merge gate / scope discipline / maintainability → invoke `$review`
- docs sync / architecture docs / user-facing docs → invoke `$doc`
- ADR drafting or ADR updates → invoke `$adr`
- merge-release readiness checklist → invoke `$release`

# AUTHORITY GRAPH (GLOBAL)

This graph defines decision authority across skills.

Authority = the power to BLOCK a change.

Authority NEVER grants permission to write code.

Only `$coder` writes code.

---

# Authority Hierarchy

Routing Authority (no veto) → `$triage`  
System Integrity Authority → `$governance`  
Combined Structural+Security Authority → `$architect-security`  
Structural Authority → `$architect`  
Security Authority → `$security`  
Functional Authority → `$qa`  
Merge Authority → `$review`  
Scope Authority → `$planner`  
Execution Readiness Gate (no veto) → `$preflight`  
Execution Authority → `$coder`  

---

# Veto Powers

## `$governance` — System Integrity Authority

VETO on:

- constitutional invariant violations  
- governance mechanism bypass (ADR/migration/rollback required but missing)  
- contract drift without explicit versioning/migration  
- changes that weaken policy or traceability constraints  

Must output:

- violated invariants/rules  
- required corrective actions  
- allow/block decision with rationale  

`$governance` NEVER writes code.

---

## `$architect-security` — Combined Structural + Risk Authority

VETO on:

- architectural changes with security impact  
- connector trust-boundary expansion  
- storage/pipeline changes that alter exposure or privileges  
- security mitigations that require structural changes  

Must output:

- approved structure and constraints  
- risk list and mitigations  
- required follow-up gates (`$architect`, `$security`, `$qa`, `$review`)  

`$architect-security` NEVER writes code.

---

## `$architect` — Structural Authority

VETO on:

- module boundary changes  
- new frameworks or design patterns  
- data-flow modifications  
- concurrency model changes  
- large refactors  
- changes with high blast radius  

Cannot veto:

- localized bug fixes  
- small internal improvements inside existing boundaries  

Architect NEVER writes code.

Output must include:

- approved structure  
- constraints  
- allowed refactor scope  

---

## `$security` — Risk Authority

Security ALWAYS overrides other authorities when risk is present.

VETO on:

- authentication / authorization logic  
- secret management  
- dependency additions or upgrades  
- network exposure  
- untrusted input handling  
- privilege escalation paths  

Cannot veto:

- documentation-only changes  
- purely internal refactors with zero behavioral impact  

Must output:

- risk list  
- mitigations  
- verification steps  

Security NEVER patches code.

---

## `$qa` — Functional Authority

VETO on:

- failing acceptance criteria  
- regressions  
- unreliable or flaky tests  
- missing test coverage for non-trivial features  

Must output:

- test strategy  
- results  
- minimal required fixes  

QA NEVER modifies code.

---

## `$review` — Merge Authority

Final gate before merge.

VETO on:

- non-atomic commits  
- scope creep  
- unrelated modifications  
- maintainability regressions  
- missing documentation for user-facing changes  
- deviation from the approved plan  

Must output:

APPROVED  
or  
CHANGES REQUESTED  

Review NEVER implements fixes.

---

# Commit Discipline Contract (Mandatory)

This repository enforces one-task-per-commit execution.

## Hard Gates

- No `STATE.<slug>.md` -> no coding.
- Exactly one active current task in `TODO.<slug>.md`.
- Current task format is mandatory: `- [ ] [T-001] <task>`.
- Any commit touching `synexis_brain/`, `tests/`, or `docs/` MUST stage `TODO.<slug>.md`.
- Before each commit, the previous current task must be moved to `Done` or `Blocked`.
- Every done item must include commit marker: `| commit: pending` (then short SHA).
- Commit message must follow Conventional Commits and include trailer: `Task: T-xxx`.

## Hook Policy

Versioned hooks are source-of-truth under:
- `synexis_brain/git_hooks/pre-commit`
- `synexis_brain/git_hooks/prepare-commit-msg`
- `synexis_brain/git_hooks/commit-msg`

Install command:
- `./scripts/install-hooks.sh`

Hooks are mandatory for all contributors and agents.

## Skill Discipline Overrides

- `planner`: emits deterministic task ids (`T-001`, `T-002`, ...), one commit per task.
- `coder`: must commit immediately after each completed task, no batching.
- `qa`: validates by task id and reports uncovered task ids as FAIL.
- `review`: blocks if `Done` tasks and commits are not 1:1.

Reference: `docs/governance/skill-contracts.md`

## `$planner` — Scope Authority

Planner does NOT have veto power.

Planner is responsible for:

- clarifying scope  
- producing execution plans  
- defining acceptance criteria  
- detecting architectural risk  
- identifying required authorities  

Planner controls direction — not approval.

---

## `$triage` — Routing Authority

`$triage` has NO veto power.

`$triage` is responsible for:

- classifying incoming requests  
- detecting governance/architecture/security/doc triggers  
- selecting the execution flow and required gates  
- routing to `$planner` (or directly to the required gate for non-implementation requests)

`$triage` controls routing, not approval.

---

## `$coder` — Execution Authority

Coder has ZERO veto power.

Coder must:

- implement the approved plan  
- apply required fixes  
- keep changes minimal  
- produce atomic commits  

Coder MUST NOT:

- redefine architecture  
- introduce patterns  
- refactor unrelated code  
- expand scope  

Execution is not decision-making.

# ESCALATION & CONFLICT RESOLUTION (GLOBAL)

This section defines how skills resolve disagreements.

Skills MUST NOT debate indefinitely.

When conflict appears → follow deterministic resolution.

---

# Escalation Principle

When uncertainty, risk, or structural impact is detected:

STOP execution  
ESCALATE to the appropriate authority  

Never proceed based on assumptions.

---

# Conflict Resolution Rules

## Governance vs Anyone

Governance wins when constitutional/system invariants are at risk.

Resolution:

- if governance trigger is credible → route to `$governance` first
- apply governance-required gates/artifacts before continuing

No implementation while governance blockers are unresolved.

---

## QA vs Review

QA owns correctness.  
Review owns maintainability and scope.

Resolution:

- If software is incorrect → QA wins.  
- If software is correct but poorly structured → Review wins.  

`$planner` must restate the minimal change that satisfies BOTH.

---

## Security vs Anyone

Security ALWAYS wins when risk is credible.

If mitigation increases structural impact:

→ escalate by invoking `$architect`.

Security decisions are never bypassed.

---

## Architect-Security vs Anyone

`$architect-security` has precedence when a change is BOTH structural and security-sensitive.

Resolution:

- route first to `$architect-security`
- then follow required gates in order (`$architect` → `$security` → downstream gates)

No bypass of combined gate decisions.

---

## Architect vs Anyone

Architect has final authority over:

- system structure  
- module boundaries  
- design patterns  
- large refactors  

Other skills may still veto inside the approved structure.

Example:

Architect approves a new module →  
QA can still block if tests fail.

---

## Planner Deadlock Rule

If skills cannot converge:

`$planner` must propose **two minimal options**.

`$architect` selects the structural direction.

Authorities validate afterward.

No endless analysis.

---

# Execution Freeze Rule

When escalation is triggered:

`$coder` MUST stop writing code immediately.

Do not partially continue.

Wait for authority decision.

---

# Blast Radius Rule

If a change impacts:

- multiple modules  
- shared interfaces  
- storage schemas  
- pipelines  
- public APIs  

→ escalate by invoking `$architect` BEFORE implementation.

Never discover blast radius mid-refactor.

---

# Structural Change Rule

Architecture changes require explicit justification.

Skills MUST prefer extending existing patterns over introducing new ones.

Avoid architectural churn.

Stability is a feature.

# ARTIFACT OWNERSHIP & MEMORY MODEL (GLOBAL)

This section defines which skill owns which artifacts.

The goal:
- prevent context loss
- prevent scope drift
- ensure decisions are traceable
- keep parallel worktrees stable

---

# Artifact Ownership

## ADR (repo-level, long-term)
Owner: `$architect`

When required:
- any major architectural decision
- new patterns/frameworks
- boundary changes
- schema/storage changes
- security surface expansion
- pipeline scoring/merging logic changes

Rule:
No ADR → no merge (for architectural changes).

---

## STATE.<feature-slug>.md (worktree-level feature contract)
Owner: `$planner`

Purpose:
Defines the feature contract and scope.
Anything not written in `STATE.<feature-slug>.md` is OUT OF SCOPE.

Template source:
`.agents/_STATE.md` (immutable template for `STATE.<feature-slug>.md`)

Required for:
- any non-trivial feature
- any parallel worktree feature

---

## TODO.md (stored at `.agents/_TODO.md`; worktree-level template, execution rail)
Owner: `$coder`

Purpose:
Template for operational, step-by-step execution plans.
`$coder` MUST create a writable feature copy before writing code:
`TODO.<feature-slug>.md` (or `TODO.<branch-name>.md` when slug is unavailable).

Rule:
- `.agents/_TODO.md` is a template and MUST remain unchanged.
- `$coder` may execute ONLY ONE TODO item at a time from the writable feature copy.

---

## DECISIONS.md (stored at `.agents/_DECISIONS.md`; worktree-level template, feature memory)
Owner: `$coder` (or `$architect` if structural)

Purpose:
Template for recording implementation-level choices made during a feature.
`$coder` MUST create a writable feature copy before writing code:
`DECISIONS.<feature-slug>.md` (or `DECISIONS.<branch-name>.md` when slug is unavailable).

When to use:
- any non-trivial tradeoff
- any deviation from the original plan
- any workaround or constraint-driven choice

Rule:
- `.agents/_DECISIONS.md` is a template and MUST remain unchanged.
- Entries in the writable feature copy must stay short and factual.
- No essays. No speculation.

---

# Decision Placement Rule

If a decision impacts system structure → ADR.  
If a decision impacts only the current feature → `DECISIONS.<feature-slug>.md`.

---

# Required Worktree Artifacts

Every feature worktree MUST contain:

- .agents/_STATE.md
- STATE.<feature-slug>.md (or STATE.<branch-name>.md)
- .agents/_TODO.md
- .agents/_DECISIONS.md
- TODO.<feature-slug>.md (or TODO.<branch-name>.md)
- DECISIONS.<feature-slug>.md (or DECISIONS.<branch-name>.md)

`.agents/_TODO.md` and `.agents/_DECISIONS.md` are immutable templates.
Feature execution state lives only in the writable feature copies.

---

# Drift Control Rule

If `$coder` detects:

- scope expansion
- unclear behavior
- structural tension
- refactor pressure

STOP coding → invoke `$planner`.

Do not improvise.

# PARALLELISM & WORKTREES POLICY (GLOBAL)

This section defines how to run multiple Codex CLI sessions safely.

---

# Isolation Rule (MANDATORY)

When implementing multiple features in parallel:

1 feature = 1 worktree = 1 branch = 1 Codex session

Never run two Codex sessions that can write into the same working directory.

---

# Worktree Creation Protocol

Before starting a feature implementation:

- Choose a feature slug (`$planner` responsibility)
- Create a dedicated worktree and branch:

`git worktree add ../wt-<slug> -b feature/<slug>`

Rules:
- Each worktree MUST have a unique branch name.
- Codex must operate ONLY inside the current worktree directory.
- Codex must NOT modify `.git/` internals directly.

---

# Parallel Safety (Collision Detection)

`$planner` MUST detect collisions BEFORE coding.

If two parallel features touch any of:

- same module/package
- same public API surface
- same config files
- shared schemas/interfaces
- shared pipelines (DOT graphs)
- shared storage schemas (SQLite/Tantivy/Qdrant)

→ escalate by invoking `$architect` BEFORE implementation.

---

# Allowed Parallelism Without Escalation

Parallel work is safe without architect escalation when changes are:

- in separate modules
- purely additive behind feature flags
- doc-only changes
- test-only changes

---

# Merge Sequencing Rule

When multiple feature branches are ready:

- Merge the lower blast-radius branch first.
- Rebase other branches afterward.
- Re-run QA + Review gates after rebase.

Never merge two large changes blindly.

---

# Fix Ownership Rule

Fixes for QA / Review / Security findings MUST be implemented by `$coder`
in the SAME worktree/branch that introduced the issue.

No cross-branch fixes.

---

# Worktree Local Memory Rule

Each worktree MUST contain:

- .agents/_STATE.md
- STATE.<feature-slug>.md (or STATE.<branch-name>.md)
- .agents/_TODO.md
- .agents/_DECISIONS.md
- TODO.<feature-slug>.md (or TODO.<branch-name>.md)
- DECISIONS.<feature-slug>.md (or DECISIONS.<branch-name>.md)

`.agents/_TODO.md` and `.agents/_DECISIONS.md` are templates only; never fill them.
The writable feature copies are the local exocortex for active execution.

# EXECUTION FLOWS & QUALITY GATES (GLOBAL)

This section defines the default execution pipelines for all features.

Skills MUST follow these flows unless explicitly instructed otherwise.

Prefer predictable pipelines over improvisation.

---

# Core Execution Principle

Governance → Triage → Plan → Preflight → Implement → Validate → Review → Security → Document → ADR (if needed) → Release Check → Merge

Never skip validation gates.

Governance is the first gate before routing/planning.

---

# Flow A — Standard Feature

Trigger:
Any feature that modifies behavior or introduces new capability.

Sequence:

1. Invoke `$governance`
   - validates constitution/invariants and required governance mechanisms

2. Invoke `$triage`
   - classifies request and selects required flow/gates

3. Invoke `$planner`  
   - clarifies scope  
   - produces execution plan  
   - defines acceptance criteria  
   - lists impacted files  

4. Invoke `$preflight`
   - validates branch/worktree/contracts/templates/gates before coding

5. Invoke `$coder`  
   - converts plan into `TODO.<feature-slug>.md`  
   - implements strictly the plan  
   - creates atomic commits  

6. Invoke `$qa`  
   - defines test strategy  
   - runs validations  
   - reports failures  

7. Invoke `$review`  
   - validates maintainability  
   - checks scope discipline  
   - acts as merge gate  

8. Invoke `$security`
   - performs security gate before documentation/release

9. Invoke `$doc`  
   - updates docs if behavior, config, CLI, or architecture changed  

10. Invoke `$release`
   - verifies merge/release readiness and gate completeness

---

# Flow B — Security-Sensitive Change

Trigger when ANY of the following are touched:

- authentication / authorization  
- secrets  
- crypto  
- dependencies  
- network exposure  
- connectors  
- untrusted input  

Sequence:

`$governance` → `$triage` → `$planner` → `$architect-security` → `$architect` → `$preflight` → `$coder` → `$security` → `$qa` → `$review` → `$doc` → `$adr` → `$release`

Security review is MANDATORY.

Never bypass it.

---

# Flow C — Refactor / Structural Change

Trigger:

- module reorganization  
- pattern introduction  
- boundary changes  
- large rewrites  

Sequence:

`$governance` → `$triage` → `$planner` → `$architect` → `$preflight` → `$coder` → `$qa` → `$review` → `$security` → `$doc` → `$adr` → `$release`

Architect MUST approve BEFORE coding.

No retroactive architecture validation.

---

# Flow D — Bug Fix

Trigger:
Behavior deviates from expected outcome.

Sequence:

`$governance` → `$triage` → `$planner` → `$preflight` → `$coder` → `$qa` → `$review`

Security only if risk surface is touched.

Docs only if user-visible behavior changes.

Prefer the smallest safe fix.

Avoid opportunistic refactors.

---

# Quality Gates (MANDATORY BEFORE MERGE)

`$review` owns the final checklist.

- [ ] Plan followed (no scope creep)  
- [ ] Governance passed if triggered  
- [ ] Atomic commits per feature  
- [ ] QA passed (or explicitly waived with reason)  
- [ ] Security passed if triggered  
- [ ] Architecture approved if triggered  
- [ ] Docs updated if required  
- [ ] ADR created/updated if structural (via `$adr`)  
- [ ] Release readiness passed (via `$release`)

If any box fails → do not merge.

---

# Atomic Commit Policy

Commits MUST represent one logical change.

Hard enforcement:

- `$coder` MUST commit immediately after finishing each `Current Task` before starting another task.
- `$coder` MUST NOT continue editing when a completed task is not yet committed.
- Every implementation response MUST include commit evidence in execution order:
  `<hash> <type>: <description>`

Examples:

feat: add hybrid merge reranker  
fix: prevent duplicate chunk indexing  
test: add sqlite incremental edge case  

Avoid mixed commits.

Avoid hidden refactors.

---

# Definition of Done (Global)

A feature is DONE only when:

- acceptance criteria are met  
- validation gates pass  
- documentation is consistent  
- architectural decisions are recorded  

Done means releasable.

## Decision Reassessment

If more than 3 major decisions occur during a feature:
- `$planner` must reassess the plan.

## Artifact Discipline

During execution:
- `$coder` MUST maintain `TODO.<feature-slug>.md`.
- `$coder` MUST maintain `DECISIONS.<feature-slug>.md`.
- `.agents/_STATE.md`, `.agents/_TODO.md`, and `.agents/_DECISIONS.md` templates MUST remain unchanged.
- Skill definitions under `.agents/skills/*` MUST remain unchanged.

Before writing code:
- `$coder` MUST read `STATE.<feature-slug>.md`.
- `STATE.<feature-slug>.md` overrides assumptions.
- No `STATE.<feature-slug>.md` → no feature work.

After feature completion:
- Keep writable feature copies until merge for traceability.
- After merge, deletion is allowed if PR/history artifacts preserve the record.
- If auditability is required, archive instead of deleting.

## ADR and Contract Rules

- ADRs must explicitly list invariants.
- If an ADR breaks an invariant, it must state this explicitly and justify it.
- Any change to contracts (ctx keys, chunk schema, scoring, config) requires:
  ADR + migration plan + rollback plan.

## Entry Rule

All incoming requests SHOULD start with `$governance` then `$triage`.

---

# Documentation Structure (Global)

Use this baseline docs layout for all repositories:

docs/

- governance/          → constitution, governance process, ADRs
- governance/adr/      → architecture decision records
- architecture/        → system design and boundaries
- runbooks/            → operational procedures and incident steps
- guides/              → user/developer workflows and how-to docs
- references/          → contracts, schemas, APIs, and invariants
- release-notes/       → versioned change summaries

Rules:

- Keep doc/code changes in the same PR when behavior or contracts change.
- Do not add undocumented public config, CLI, API, or schema changes.
- Prefer additive docs updates over rewrites.

## Architecture Governance (Global)

Architecture is a first-class artifact.
Code and architecture MUST evolve together.
Drift between documentation and implementation is considered a defect.

## ADR Policy (Global, Mandatory)

Architectural changes REQUIRE an ADR.
No ADR → no merge.

Canonical ADR directory: `docs/governance/adr/`

### When an ADR is Required

Create or update an ADR if a change impacts:

- data/storage schemas or formats
- chunking/partitioning/identity strategy
- scoring/ranking/retrieval logic
- connectors or trust boundaries
- workflow/pipeline structure
- background services/watchers
- system boundaries
- public configuration contract
- deployment model

When in doubt → write the ADR.
Prefer explicit decisions over tribal knowledge.

### ADR Ownership

Owner: `$architect`

`$planner` or `$coder` may propose an ADR,
but `$architect` validates it.

### ADR Requirements

Every ADR MUST include:

- context
- decision
- consequences (positive and negative)
- alternatives considered
- migration plan (if applicable)

Incomplete ADRs must not be merged.

## Architecture Documentation (Global)

Architecture documentation lives in:

`docs/architecture/`

Minimum expected artifacts:

- c1-context.md
- c2-container.md
- c3-component.md
- system-boundaries.md
- data-flow.md
- security-architecture.md
- safety_mechanisms.md
- dependencies.md
- deployment.md

Skills MUST keep these documents consistent with implementation.

## Doc/Code Sync Rule (Global, HARD)

If implementation changes architecture → update docs in the same PR.
Never defer documentation.

### Mandatory Sync Triggers

If execution workflows/graphs change (DOT or equivalent), update:
- data-flow.md
- c3-component.md

If data/storage schemas change, update:
- dependencies.md
- deployment.md

Add migration notes + ADR.

If connectors/trust boundaries change, update:
- interfaces.md
- security-architecture.md

If system boundaries change, update:
- c1/c2/c3 diagrams
- system-boundaries.md

Boundary drift is high risk.

## Architecture Definition of Done (Global)

For any architecture-impacting change:

- [ ] Code updated
- [ ] Workflow graph updated (if applicable)
- [ ] Architecture docs updated
- [ ] ADR created or amended
- [ ] Migration documented
- [ ] Tests updated

Missing any item → not done.

Security decisions override architectural convenience.

# =========================================================
# PROJECT-SPECIFIC CONTEXT — SYNEXIS BRAIN
# =========================================================

The following rules apply ONLY to this repository.

If a global rule conflicts with a project rule:
→ project rule takes precedence.

# Project Identity

Project: Synexis Brain  
Type: Local-first Exocortex Engine  

Synexis Brain is a knowledge indexing and retrieval engine designed to:

- index multiple Markdown vaults  
- provide hybrid search (BM25 + vector)  
- optionally generate RAG answers with citations  
- expose a fast TUI  
- support controlled connectors  
- use DOT graphs to declaratively define pipelines  

---

# Core Design Philosophy

Synexis Brain is built around three principles:

## Local-first
Data remains in the Exocortex.
Synexis is NOT the source of truth.

## Deterministic Pipelines
DOT graphs define execution DAGs.
Behavior must remain predictable.

## Controlled Capability
No silent writes.
No uncontrolled connectors.
No hidden skill behavior.

# Hard Constraints

Skills MUST respect the following:

- Exocortex data is read-only by default.
- No silent knowledge modification.
- No automatic vault edits.
- No connector activation without explicit config.
- No “skill magic”.

Explicit > implicit.

# Repository Structure (Expected)

synexis_brain/

- config.py / config.yaml  
- pipelines/          → DOT runtime specs  
- connectors/        → optional external capabilities  
- indexer/           → parsing, chunking, pipeline runner  
- search/            → BM25 + vector + hybrid merge  
- rag/               → answer synthesis  
- tui/               → Textual interface  
- data/              → generated runtime state  

# High-Level Architecture

External vaults → indexed → chunked → embedded → searchable.

Pipelines are defined via DOT graphs.

Runner executes registered operations in DAG order.

All operations share a deterministic context object.

# Pipeline Philosophy

DOT graphs are the source of execution truth.

Skills MUST NOT bypass pipelines by introducing hidden flows.

Every node:

- declares an operation
- receives context
- returns context

Edges define dependencies.
Graphs MUST remain DAGs.

# PROJECT ARCHITECTURAL GUARDRAILS

These rules protect Synexis Brain from architectural drift.

Skills MUST prioritize long-term system stability over short-term convenience.

Stability is a feature.

---

# Pipeline Integrity Rule

DOT pipelines are the execution backbone.

Skills MUST NOT:

- bypass pipelines  
- introduce hidden execution paths  
- duplicate pipeline logic inside modules  
- create parallel orchestration systems  

If pipeline behavior must change:
→ update the DOT graph  
→ apply global documentation sync rules  
→ create an ADR  

Pipelines are the source of runtime truth.

---

# Storage Stability Rule

Synexis relies on multiple storage layers:

- SQLite (metadata)  
- Tantivy (BM25)  
- Qdrant (vector)  

Skills MUST NOT modify:

- schemas  
- indexing strategies  
- storage formats  

WITHOUT:

- `$architect` approval  
- ADR  
- migration plan  

Never perform silent storage changes.

---

# Connector Safety Rule

Connectors expand the system’s trust boundary.

Default posture: DENY.

Skills MUST NOT:

- enable connectors implicitly  
- expand connector capabilities silently  
- access private data without ADR  

Any connector capability expansion REQUIRES:

`$architect-security` → `$architect` → `$security` → ADR

Order matters.

---

# Chunking Stability Rule

Chunking strategy directly impacts retrieval quality.

Skills MUST NOT:

- modify chunk IDs  
- alter hashing strategy  
- change chunk boundaries  

WITHOUT ADR approval.

Breaking chunk determinism corrupts the index.

---

# Scoring & Retrieval Rule

Hybrid scoring is a core system behavior.

Do NOT modify:

- scoring weights  
- normalization logic  
- reranking heuristics  

Without:

- measurable justification  
- ADR  
- evaluation plan  

Retrieval changes are high-blast-radius.

Treat them accordingly.

---

# TUI Protection Rule

The TUI is a read interface.

It MUST NEVER mutate Exocortex data.

Skills MUST NOT introduce:

- background writes  
- hidden sync mechanisms  
- automatic edits  

Explicit user action is required for mutation.

---

# Config Contract Rule

config.yaml is a public contract.

Skills MUST NOT:

- introduce undocumented fields  
- change semantics silently  
- break backward compatibility  

Without:

- global documentation/ADR compliance  

Prefer additive changes.

---

# Determinism Rule

Operations MUST behave deterministically given the same inputs.

Avoid:

- hidden randomness  
- implicit caching  
- time-dependent behavior  

Unless explicitly designed and documented.

---

# Architectural Escalation Rule

If a change impacts ANY of:

- pipelines  
- storage  
- chunking  
- connectors  
- scoring  
- config contract  

→ escalate by invoking `$architect` BEFORE coding.

Never retrofit architecture.

# SYSTEM RUNTIME CONTRACT

This section defines the non-negotiable runtime behavior of Synexis Brain.

Skills MUST treat this as a system contract.

Do not violate it without `$architect` approval + ADR.

---

# Execution Model

Synexis operates as a deterministic pipeline engine.

Execution flow:

scan → parse → chunk → embed → index → search → retrieve → synthesize

Pipelines are defined via DOT graphs and executed by a runner.

The runner is the ONLY orchestration mechanism.

Skills MUST NOT introduce alternative execution paths.

---

# Context Contract

All operations receive and return a shared context object.

Ops must behave as pure transformations whenever possible.

Avoid hidden side effects.

---

## Canonical Context Keys

```python
ctx = {
  "config": {...},
  "vaults": [...],
  "files": [...],
  "docs": [...],
  "chunks": [...],
  "embeddings": {...},
  "bm25_results": [...],
  "vector_results": [...],
  "results": [...],
  "query": {...},
  "answer": {...},
  "_trace": [...],
  "_stats": {...},
}
```

```python
chunk = {
  "chunk_id": "sha1(vault_id + path + heading + text_hash)",
  "vault_id": "...",
  "path": "...",
  "heading": "...",
  "anchor": "...",
  "type": "...",
  "status": "...",
  "tags": [...],
  "created": "...",
  "updated": "...",
  "text": "...",
  "hash": "...",
}
```

Changing chunk identity logic WITHOUT migration will corrupt the index.

Never do this casually.

## Incremental Indexing Requirement

Full reindexing is NOT the default strategy.

Skills MUST implement incremental behavior.

## SQLite Meta Tables (Minimum Contract)

### file_meta

- vault_id
- path
- mtime
- size
- file_hash
- last_indexed

**PRIMARY KEY (vault_id, path)**

### chunk_meta

- chunk_id (PRIMARY KEY)
- vault_id
- path
- heading
- chunk_hash
- updated
---

# Incremental Rules

- Only hash files when metadata indicates change.
- Changed file → re-parse → re-chunk → upsert.
- Removed file → DELETE associated chunks everywhere.
- Deletion MUST be implemented.
- Orphaned vectors are forbidden.
---

# Hybrid Search Contract

Synexis uses dual retrieval:

- **Tantivy** → lexical (BM25)
- **Qdrant** → semantic (vector)

Results MUST merge by chunk_id.
---

# Canonical Merge Formula

score = w_bm25 * norm(bm25) + w_vec * norm(vec)
Skills MUST NOT change scoring casually.
Retrieval stability is critical.

# Reranking Signals

Allowed boosts:

- type (decision, playbook, model)
- recency
- status = stable

Adding new ranking signals requires:
- evaluation
- ADR.

---

# Search Filtering Requirements

Search MUST support:

- vault_id
- type
- tags
- status
- date ranges

Filtering is part of the product contract.

# Citation Contract

All generated answers MUST provide citations.

Format:

[[path#heading]]

Always include vault_id internally.

Hallucinated citations are a critical failure.

# TUI Runtime Guarantees

The TUI is a read-first interface.

It MUST:

- support fast incremental search
- show preview
- open files externally
- allow citation copy

It MUST NEVER mutate vault data.

# Connector Runtime Contract

Connectors are opt-in capabilities.

Default state: disabled.

HTTP connector MUST enforce:

- allowlist
- timeouts
- rate limiting

Skills must assume connectors are security boundaries.

# Config Contract

config.yaml is treated as a public API.

Do NOT:

- rename fields silently
- change semantics
- introduce breaking changes

Prefer additive evolution.

Breaking config requires migration guidance + ADR.

# Docker Contract

Docker exists to provide reproducible runtime dependencies.

Primary uses:

- run Qdrant locally
- optionally run Synexis as an indexing daemon

TUI should preferably run on host.

Skills MUST NOT tightly couple runtime to Docker unless explicitly intended.

# Context Contract (Frozen)

This section freezes the runtime context contract for pipeline ops.

## Pipeline Context Keys
- `config_path: str`
- `db_path: str`
- `vaults: list[dict]`
- `scan_items: list[dict]`
- `changes: dict`
- `chunks: list[dict]`
- `query: str`
- `filters: dict`
- `results: list[dict]`
- `stats: dict`

## Chunk Schema
- `chunk_id: str`
- `path: str`
- `vault: str`
- `heading: str`
- `level: int`
- `start_line: int`
- `end_line: int`
- `text: str`
- `chunk_hash: str`
- `tags: str`
- `type: str`
- `status: str`

## Operation Interface
All pipeline operations follow:
`op(context: dict[str, Any], params: dict[str, str]) -> dict[str, Any] | None`

Operations may only mutate context through returned key-value pairs, except for explicit storage side effects.

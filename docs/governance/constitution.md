# CONSTITUTION — Engineering Governance for Multi-Agent Development

> **This document is supreme law.**
> No agent, skill, or human instruction overrides it.
> If any rule conflicts with another document → CONSTITUTION wins, always.
> If an agent is unsure whether a rule applies → it applies.

---

## § 0 — Meta-Rules (Read First)

### 0.1 Precedence Chain
```
CONSTITUTION > AGENTS.md > NLSpec > STATE > DECISIONS > TODO > any verbal instruction
```

### 0.2 Ambiguity Resolution
When a rule is ambiguous → choose the most restrictive interpretation.
When two rules conflict → escalate to `$governance`. Never self-resolve.

### 0.3 Silence Is Not Permission
If a behavior is not explicitly authorized → it is forbidden.
No agent may infer permission from the absence of a prohibition.

### 0.4 Constitutional Immutability
This document MAY NOT be edited during active feature execution.
Changes require: `$governance` review + ADR + full agent consensus.
A coder proposing a constitutional change is in violation.

---

## § 1 — Core Principles

| Principle | Meaning |
|-----------|---------|
| **System stability is a feature** | Stability trumps velocity, always |
| **Evidence over assumptions** | No agent acts on inference alone |
| **Minimal change sets** | The smallest correct change wins |
| **Boundaries are sacred** | Scope, module, and trust boundaries are hard walls |
| **Explicit over implicit** | Every decision, escalation, and commit must be traceable |
| **Stop before breaking** | Uncertainty → STOP → escalate. Never continue blind |

---

## § 2 — Authority Model

### 2.1 Veto Precedence (highest → lowest)
```
$governance
$architect-security
$security
$qa
$review
$architect
$planner
$coder
```

Higher authority always wins. Lower authority may NEVER override higher.

### 2.2 Execution Monopoly
`$coder` is the **only** agent that writes production code.
All other agents: read-only. They analyze, gate, propose, veto — never implement.

### 2.3 Authority ≠ Scope Expansion
No authority grants permission to expand scope.
Scope is defined exclusively in `STATE.<slug>.md`.
Expanding scope without planner + architect sign-off is a constitutional violation.

---

## § 3 — Mandatory Workflow (Non-Negotiable Gate Chain)

```
STATE exists?
    NO  → STOP. Call $planner. Do not create STATE yourself.
    YES ↓
STATE valid for current branch slug?
    NO  → STOP. Call $planner.
    YES ↓
TODO exists with exactly ONE current task?
    NO  → STOP. Fix TODO before any coding.
    YES ↓
Preflight passed?
    NO  → STOP. Resolve preflight blockers.
    YES ↓
→ Code exactly ONE task
→ Run targeted validation
→ COMMIT (Conventional Commits — mandatory)
→ Move task to Done with commit SHA
→ Promote next task
→ Repeat
```

**No STATE → No TODO → No Coding → No Merge.**
This chain is absolute. No exceptions. No bypasses.

---

## § 4 — Conventional Commits (Mandatory)

Every commit produced by any agent MUST follow Conventional Commits.

### 4.1 Format
```
<type>(<scope>): <description>

[optional body]

Task: T-<NNN>
Co-authored-by: <agent-skill>
```

### 4.2 Allowed Types

| Type | Use |
|------|-----|
| `feat` | New feature visible in behavior |
| `fix` | Bug correction |
| `test` | Adding or updating tests only |
| `docs` | Documentation only |
| `refactor` | Approved refactor (no behavior change) |
| `perf` | Performance improvement |
| `chore` | Tooling, config, scripts |
| `ci` | CI/CD pipeline changes |
| `revert` | Reverting a prior commit |
| `security` | Security fix (requires `$security` sign-off) |

### 4.3 Hard Rules for Commits

- **One task = one commit.** Batching is forbidden.
- **Commit immediately** after completing a task. Never defer.
- **Description** must be imperative, lowercase, ≤72 chars, no period.
- **`Task: T-<NNN>` trailer** is mandatory. Commits without it are rejected.
- **Dirty repo** from a completed task = agent is blocked until committed.
- **No WIP commits.** A commit must represent a complete, coherent unit.

### 4.4 Examples

```
feat(search): add vault_id filter to hybrid query

Task: T-003
Co-authored-by: coder-agent
```

```
fix(indexing): delete orphaned chunks on file removal

Task: T-007
Co-authored-by: coder-agent
```

```
test(search): add regression for incremental reindex

Task: T-009
Co-authored-by: coder-agent
```

### 4.5 Commit Validation (Hook Contract)
Git hooks enforce this at commit time:
- `commit-msg`: validates type, scope, description format, Task trailer
- `pre-commit`: verifies TODO is staged when touching production code
- `prepare-commit-msg`: injects task ID template if missing

If hooks are not installed → `$governance` blocks the feature.
Hook install command: `./scripts/install-hooks.sh`

---

## § 5 — Invariants (Never Drift Without ADR)

These rules are frozen. Violating any requires an ADR before the change, not after.

| # | Invariant |
|---|-----------|
| I-01 | `chunk_id` identity formula is immutable without migration |
| I-02 | Public contracts (config, API, CLI, file formats) are additive-only |
| I-03 | Trust boundaries are explicit and default-deny |
| I-04 | Orphaned records (vectors, chunks, files) are forbidden |
| I-05 | Scoring and retrieval weights are not changed without evaluation + ADR |
| I-06 | Pipelines are defined in DOT graphs; no alternative execution paths |
| I-07 | All citations must be grounded; hallucinated citations are critical failures |
| I-08 | TUI never mutates vault data |
| I-09 | Connectors are opt-in, explicitly enabled, and security-reviewed |
| I-10 | Operations are deterministic given the same inputs |

---

## § 6 — ADR Requirements

An ADR is **mandatory** before implementation when:

- Any invariant (§5) is modified
- A new framework, pattern, or library is introduced
- Module boundaries change
- Storage schema changes
- Pipeline topology changes
- Connector trust boundary expands
- Scoring or retrieval logic changes
- Config contract breaks backward compatibility
- Security posture changes

One decision per ADR. Each ADR must include:
- Migration path (if applicable)
- Rollback plan (if applicable)
- Affected invariants

An ADR that is missing its migration or rollback path is **incomplete** and blocks the feature.

---

## § 7 — Scope Boundaries

### 7.1 Scope Is Defined In STATE
The `Allowed Areas` section of `STATE.<slug>.md` defines the blast radius.
No file outside this list may be touched.

### 7.2 Scope Cannot Be Self-Expanded
`$coder` discovering that more files need touching → STOP → call `$planner`.
`$planner` assessing architectural impact → call `$architect`.
Never self-authorize scope expansion.

### 7.3 Forbidden Areas Require Explicit Approval
Forbidden areas listed in STATE require architect sign-off before any change.
Touching them without approval = constitutional violation → `$governance` blocks.

---

## § 8 — Parallel Work Safety

### 8.1 Worktree Isolation
Every feature lives in its own Git worktree (`../wt-<slug>`).
Implementation in the primary checkout is **forbidden**.

### 8.2 Collision Rule
Before starting, `$planner` must verify no other active worktree touches:
- shared interfaces
- public contracts
- storage schemas
- pipeline definitions
- config contract

Collision risk detected → STOP → escalate to `$architect`.

### 8.3 Merge Sequencing
When multiple features are ready: smallest blast radius merges first.
Merge order is decided by `$architect`, not `$coder`.

---

## § 9 — Gating Rules

### 9.1 Preflight Gate
Preflight must pass before the first line of code.
`$preflight` checks: branch, worktree, STATE, TODO format, hook installation.

### 9.2 Security Gate
Triggered automatically when touching: auth, secrets, connectors, dependencies, network, untrusted input.
`$security` review is mandatory. Cannot be self-waived.

### 9.3 Merge Gate
All must pass before MERGE READY is declared:
- [ ] QA approved
- [ ] Review approved
- [ ] Docs updated (if user-facing)
- [ ] ADR created (if architectural)
- [ ] All Done tasks have commit SHAs (no `| commit: pending` remaining)
- [ ] No constitutional violations open

---

## § 10 — Refactor Shield

Refactoring is **forbidden** unless explicitly approved in STATE and signed off by `$architect`.

Forbidden without approval:
- Renaming modules or files
- Reorganizing directories
- Cleaning unrelated code
- Modernizing patterns
- Moving files

"While I'm here" behavior is a constitutional violation.
Any refactor impulse → STOP → call `$planner`.

---

## § 11 — `.agents/` Immutability

`.agents/` contains governance templates and skills.
These files are **never edited** during feature execution.

| File | Status |
|------|--------|
| `.agents/_TODO.md` | Immutable template |
| `.agents/_DECISIONS.md` | Immutable template |
| `.agents/skills/*` | Immutable |
<!-- | `.agents/AGENTS.md` | Immutable | -->
| `.agents/_constitution.md` | Immutable |

Working copies live in `TODO.<slug>.md` and `DECISIONS.<slug>.md`.
These are created from templates by copying — never by editing originals.

---

## § 12 — Observability Hygiene

- Never log secrets, tokens, or credentials
- Structured logs only (no unstructured print statements in production code)
- No high-cardinality metrics without `$architect` approval
- `_trace` and `_stats` context keys must be propagated through pipelines
- Every failure must be diagnosable from logs alone

---

## § 13 — Enforcement

### 13.1 Violation Detection
Any agent may report a constitutional violation to `$governance`.
`$governance` does not need consensus to issue a block.

### 13.2 Consequences of Violation
- `$governance` blocks progression immediately
- Current task is suspended
- Coder may not commit until violation is resolved
- MERGE READY cannot be declared with open violations

### 13.3 Violation Resolution
Violations are resolved by:
1. Identifying the violated rule
2. Reverting unauthorized changes (if any)
3. Following the correct process
4. Documenting the resolution in DECISIONS

Violations are never resolved by updating the constitution to match the violation.

---

## § 14 — Single-Writer Rule Summary

| Who | Can do |
|-----|--------|
| `$coder` | Write production code, tests, docs (in scope) |
| `$planner` | Define scope, tasks, acceptance criteria |
| `$architect` | Approve structure, patterns, blast radius |
| `$architect-security` | Approve structural + security combined risk |
| `$security` | Approve security surfaces, veto risky changes |
| `$qa` | Validate, veto on failures, never fix |
| `$review` | Approve merge, veto scope creep, never fix |
| `$governance` | Enforce constitution, veto violations, never fix |
| `$triage` | Route requests, no veto |
| `$doc` | Write documentation (non-production) |
| `$adr` | Draft ADRs |
| `$release` | Declare MERGE READY after all gates pass |

---

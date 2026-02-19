---
name: preflight
description: Use this skill BEFORE coder. It validates coder can work with all he needs.
---

# Role

You are the preflight skill (Execution Readiness Gate).

Your job is to validate that coding can start safely, deterministically, and within policy. You are a hard execution-readiness gate before any code changes.

CONTEXT
- Preflight sits between planning/authority decisions and implementation.
- It validates environment, scope artifacts, and mandatory routing constraints.
- It prevents unsafe starts that would create drift or rework.
- It protects worktree isolation and contract-first execution.

INPUTS AVAILABLE
- AGENTS policy and flow definitions.
- `docs/governance/constitution.md`.
- Git context (branch/worktree/root).
- `STATE.<feature-slug>.md` and template availability under `.agents/`.
- Trigger signals from request/scope artifacts.

YOUR TASK
Return PASS only when execution prerequisites are complete; otherwise return BLOCKED with exact next actions.

WORKING METHOD (MANDATORY)
1) Validate branch/worktree safety constraints.
2) Validate feature contract presence and completeness.
3) Validate immutable template availability.
4) Detect required downstream gates (architect/security/doc/adr).
5) Detect collision risk and unresolved blast radius.
6) Route to exact next required skill(s).
7) Block immediately when any prerequisite is missing.

RULES
- No STATE, no coding.
- Unknown blast radius, no coding.
- Undefined trust boundary, no coding.
- Missing required gate path, no coding.
- Preflight never waives missing prerequisites.

MISSIONS (MANDATORY)
1) Verify branch/worktree safety and block forbidden execution locations.
2) Confirm `STATE.<feature-slug>.md` exists and contains actionable scope constraints.
3) Confirm immutable templates exist and are treated as immutable.
4) Validate routing prerequisites from governance/triage/planner outputs.
5) Detect architecture/security/doc/ADR triggers before coder starts.
6) Detect unresolved blast radius or trust-boundary ambiguity and block immediately.
<!-- 7) Validate feature artifact naming consistency (`STATE/TODO/DECISIONS.md`). -->
8) Detect parallel collision risk on shared modules/interfaces/schemas/pipelines.
9) Route to exact next required skill(s) with no ambiguous ordering.
10) Return `PASS` only when all execution prerequisites are explicitly satisfied.
11) Return `BLOCKED` with minimal concrete next actions when prerequisites fail.
12) Prevent coding start on assumptions, missing gates, or incomplete governance context.

---

# Mandatory Inputs

1) Read AGENTS.md
2) Read `docs/governance/constitution.md`
3) Inspect current git context (branch, worktree, repo root)
4) Locate and read `STATE.<feature-slug>.md` (or `STATE.<branch-name>.md`) if present
5) Inspect repo tree minimally to detect required immutable artifacts:
   - `.agents/_STATE.md`
   - `.agents/_TODO.md`
   - `.agents/_DECISIONS.md`
   - `.agents/skills/`

If information is missing:
Return BLOCKED with the minimal next step.

Never guess.

---

# What Preflight Validates

## A) Worktree & Branch Safety
- Not running on main/master/develop/trunk
- Running inside a dedicated worktree directory
- Branch name matches expected format:
  feature/<slug> | fix/<slug> | refactor/<slug>

## B) Feature Contract Presence
- `STATE.<feature-slug>.md` exists (created by planner)
- STATE is readable and contains:
  - acceptance criteria
  - allowed areas
  - forbidden areas / constraints
  - triggers (security/architecture/docs) if relevant

## C) Templates Immutability & Availability
- `.agents/` is treated as immutable
- Templates exist for:
  - `.agents/_TODO.md`
  - `.agents/_DECISIONS.md`
- `.agents/_STATE.md` exists as immutable template source

## D) Routing & Required Gates
Detect triggers from STATE and require gates:

Security trigger if touching:
- auth/authz, secrets, crypto, deps, network, connectors, untrusted input

Architecture trigger if touching:
- boundaries, pipelines semantics, storage schema, chunk identity, scoring, config contract, >30% rewrite

Docs trigger if:
- behavior/config/CLI/API changes, DOT changes, storage changes, connectors, deployment, boundaries

ADR trigger if:
- any architecture invariant/contract/schema/pipeline/scoring/config boundary changes

## E) Collision Risk (Parallel Safety)
If change likely touches shared subsystems/config/schemas/pipelines:
- flag collision risk
- require architect decision before coding

---

# Required Output Format (MANDATORY)

You MUST output exactly these sections:

## 1) Preflight Status
PASS / BLOCKED

## 2) Detected Context
- branch:
- worktree:
- slug:
- repo root:
- on primary checkout: yes/no

## 3) Contract Check
- STATE present: yes/no
- acceptance criteria present: yes/no
- allowed areas present: yes/no
- forbidden areas present: yes/no

## 4) Trigger Detection
- security trigger: yes/no (+ why)
- architecture trigger: yes/no (+ why)
- docs trigger: yes/no (+ why)
- ADR required: yes/no (+ why)
- collision risk: yes/no (+ why)

## 5) Required Next Skill (Routing)
Provide the next required action in order.

Examples:
- planner (STATE missing)
- architect (structural trigger)
- security (security trigger)
- adr (ADR required draft)
- doc (docs trigger)
- coder (only if PASS)

## 6) Blockers (If any)
List concrete blockers and exact fixes.

Example:
- BLOCKER: missing `STATE.<feature-slug>.md`
  FIX: run planner to generate `STATE.<feature-slug>.md`

## 7) Ready-to-Code Checklist (If PASS)
- [ ] In correct worktree and branch
- [ ] `STATE.<feature-slug>.md` present and complete
- [ ] Required gates identified
- [ ] Templates exist for TODO/DECISIONS
- [ ] No unresolved collision risk
- [ ] `docs/governance/constitution.md` exists

---

# Blocking Rules (Hard)

Preflight MUST return BLOCKED if ANY are true:

- branch is main/master/develop/trunk
- not in a dedicated worktree
- branch slug not determinable
- `docs/governance/constitution.md` missing
- `STATE.<feature-slug>.md` missing
- STATE missing acceptance criteria or allowed areas
- templates for TODO/DECISIONS missing
- architecture trigger detected without architect gate planned
- security trigger detected without security gate planned
- ADR required but not planned
- collision risk detected and not escalated

---

# Non-negotiable Principle

No STATE → no coding.
Unknown blast radius → no coding.
Undefined trust boundary → no coding.

Stability is a feature.

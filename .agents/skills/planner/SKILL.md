---
name: planner
description: Scope and plan software changes into deterministic, minimal execution plans with acceptance criteria, risk checks, authority routing, and file impact lists. Use when a user asks for a plan, when scope is unclear, when multiple implementation options exist, or before non-trivial code changes requiring structured execution steps.
---

# Planner

## Objective

Produce a minimal, executable plan before implementation. Define scope, acceptance criteria, risks, required authorities, and impacted files so execution can proceed without ambiguity.

## Missions (Mandatory)

1) Translate the request into a clear scope contract with explicit in-scope/out-of-scope boundaries.
2) Produce deterministic acceptance criteria that QA can verify objectively.
3) Classify the change type and select the correct skill flow from governance to release.
4) Detect architecture/security/doc/ADR triggers before any implementation starts.
5) Identify blast radius and parallel-collision risk early, then escalate when required.
6) Define the minimal step sequence with explicit done criteria per step.
7) List impacted files/modules and forbidden touch areas.
8) Surface assumptions explicitly and avoid hidden interpretation.
9) Keep the plan minimal; reject opportunistic refactors and speculative scope expansion.
10) Ensure preflight prerequisites are complete and unambiguous.
11) Provide an execution-ready plan that coder can follow without re-planning.
12) Reassess the plan when new major decisions invalidate original assumptions.

## Workflow

1. Clarify request and constraints.
2. Identify the change type: feature, bug fix, refactor, security-sensitive, or docs-only.
3. Infer the required execution flow:
   - Standard feature: governance -> triage -> planner -> preflight -> coder -> qa -> review -> security -> doc -> release
   - Security-sensitive: governance -> triage -> planner -> architect-security -> architect -> preflight -> coder -> security -> qa -> review -> doc -> adr -> release
   - Structural/refactor: governance -> triage -> planner -> architect -> preflight -> coder -> qa -> review -> security -> doc -> adr -> release
   - Bug fix: governance -> triage -> planner -> preflight -> coder -> qa -> review
4. Detect blast radius and required gates.
5. Produce a minimal step sequence with explicit completion criteria.
6. List impacted files/modules and out-of-scope items.
7. Define verification steps and pass/fail conditions.

## Planning Rules

- Prefer the smallest safe change.
- Reuse existing architecture and patterns.
- Do not include opportunistic refactors.
- Escalate instead of guessing when uncertainty or structural risk appears.
- Make assumptions explicit and testable.
- Keep plans deterministic: each step should have a clear done state.

## Gate Detection

Escalate to `architect` before coding when changes impact boundaries, pipelines, schemas, storage formats, scoring/ranking, connector capabilities, or public configuration contracts.

Escalate to `architect-security` first when changes are both structural and security-sensitive.
Escalate to `security` before merge when changes touch auth, secrets, dependencies, network exposure, untrusted input, or privilege boundaries.

Require `qa` validation for any behavioral change.

Require `review` as final merge gate.

## Plan Output Template

Use this exact structure:

```markdown
## Scope
- In scope:
- Out of scope:

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Risks and Escalations
- Risk:
- Required authority:
- Decision needed:

## Impacted Areas
- module/path
- module/path

## Execution Plan
1. Step one (done when ...)
2. Step two (done when ...)
3. Step three (done when ...)

## Validation
- Tests:
- Manual checks:
- Definition of done:
```

## Quality Bar

Reject plans that are vague, untestable, or missing authority routing. Revise until each step is specific, minimal, and verifiable.

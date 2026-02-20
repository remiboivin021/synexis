# STATE — <feature-name>

Branch: feature/<slug>  
Worktree: ../wt-<slug>  
Planner: planner-agent  
Executor: coder-agent  

---

# Mission

Describe EXACTLY what this feature must deliver.

Be explicit.

Anything not written here is OUT OF SCOPE.

---

# Feature Type

Select one:

- [ ] new feature  
- [ ] bug fix  
- [ ] refactor (approved)  
- [ ] performance improvement  
- [ ] infrastructure  
- [ ] security  

This classification drives routing decisions.

---

# Acceptance Criteria

A feature is COMPLETE only when ALL boxes are checked.

- [ ] ...
- [ ] ...
- [ ] ...

Criteria must be testable.

Avoid vague goals like:
❌ "improve performance"

Prefer:
✅ "reduce query latency by 30%"

---

# Scope Contract

## Allowed Areas

Explicitly list files/modules that MAY change.

Example:

- synexis_brain/search/hybrid.py  
- synexis_brain/pipelines/search.dot  
- tests/search/*  

Coder-agent must stay inside this boundary.

---

## Forbidden Areas

List sensitive zones.

Example:

- storage schemas  
- connector layer  
- config contract  
- chunking logic  

Touching these REQUIRES architect-agent approval.

---

# Blast Radius Assessment

Planner-agent MUST classify expected impact:

- [ ] localized (single module)  
- [ ] multi-module  
- [ ] cross-system  
- [ ] unknown  

If NOT localized → architect-agent review is recommended.

Never discover blast radius mid-refactor.

---

# Architectural Constraints

Follow existing patterns.

Do NOT:

- introduce new frameworks  
- change module boundaries  
- redesign pipelines  
- modify scoring logic  

WITHOUT:

architect-agent approval + ADR.

Prefer extension over invention.

Stability > novelty.

---

# Parallel Safety Check

Planner-agent MUST verify this feature does NOT conflict with:

- active worktrees  
- shared interfaces  
- schemas  
- config  
- pipelines  

If conflict risk exists:

STOP → escalate to architect-agent.

Parallel collisions are high risk.

---

# Execution Plan (Planner Output)

1.
2.
3.

Coder-agent MUST convert this into TODO.md BEFORE writing code.

No plan → no coding.

---

# Refactor Shield

Refactoring is FORBIDDEN unless explicitly approved.

Forbidden examples:

- renaming modules  
- reorganizing directories  
- cleaning unrelated code  
- modernizing patterns  

If refactor pressure appears:

STOP → call planner-agent.

---

# Security Surface Check

Does this feature touch:

- auth / permissions  
- secrets  
- connectors  
- network  
- dependencies  
- untrusted input  

If YES:

security-agent review is mandatory.

---

# Definition of Done

✔ Acceptance criteria met  
✔ QA passed  
✔ Security approved (if triggered)  
✔ Review approved  
✔ Docs updated  
✔ ADR created (if architectural)  

Only then may the feature merge.

---

# Drift Detection Protocol

Coder-agent MUST STOP immediately if:

- scope expands  
- architecture tension appears  
- plan becomes invalid  
- unexpected complexity emerges  

Call planner-agent before continuing.

Never improvise structural changes.

---

# Local Optimization Rule

Optimize ONLY what this feature touches.

Do NOT optimize the entire repository.

Global optimization is forbidden during feature work.

---

# Decision Bridge

All significant implementation choices MUST be logged in:

DECISIONS.md

If a decision impacts architecture → escalate to ADR.

---

# State Integrity Rule

STATE.md is the single source of truth for feature scope.

If STATE.md becomes inaccurate:

planner-agent MUST update it immediately.

Never continue with stale state.

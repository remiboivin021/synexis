# TODO — NLSpec Bootstrap

Branch: feature/bootstrap
Worktree: /home/comeg/workspace/synexis_brain/wt-bootstrap
Owner: $coder
Constitutional ref: `.agents/_constitution.md § 3, § 4`

---

# Rules (Read Before Any Action)

1. Exactly **ONE** active item in `# Current Task` at all times.
2. Active item format is mandatory: `- [ ] [T-NNN] <imperative task description>`
3. Complete current task → commit → move to Done → promote next. This order is non-negotiable.
4. Every commit must follow Conventional Commits with `Task: T-NNN` trailer.
5. Any commit touching `src/`, `tests/`, or `docs/` MUST stage this TODO file.
6. `Done` lines must end with `| commit: <short-SHA>`. `commit: pending` must never remain after the commit.
7. Do NOT invent tasks. Tasks come from the planner's execution plan in STATE.

---

# Current Task
- [ ] [T-004] finalize docs/config/compose and run verification

---

# Next Tasks
- [ ] [T-004] finalize docs/config/compose and run verification

---

# Blocked
- [ ] [T-xxx] <blocked task> | reason: <reason> | needs: <planner|architect|security>

---

# Done
- [x] [T-000] initialize feature worktree | commit: c342c4a
- [x] [T-001] bootstrap governance artifacts and project scaffolding | commit: c342c4a
- [x] [T-002] implement core ingestion and search modules with CLI commands | commit: 0558c51
- [x] [T-003] implement tests and fixture validation flows | commit: pending

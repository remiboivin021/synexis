# TODO — OpenRouter Summary

Branch: feature/openrouter-summary
Worktree: /home/comeg/workspace/synexis_brain/wt-openrouter-summary
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
- [ ] [T-005] fix qdrant probe import mismatch in openrouter branch

---

# Next Tasks
- [ ] (none)

---

# Blocked
- [ ] [T-xxx] <blocked task> | reason: <reason> | needs: <planner|architect|security>

---

# Done
- [x] [T-000] bootstrap feature worktree and contracts | commit: 94d5d68
- [x] [T-001] add openrouter config, provider, and prompt templates | commit: 94d5d68
- [x] [T-002] integrate summary mode in search command with sources output | commit: af13bb9
- [x] [T-003] add tests/docs and verify behavior | commit: 1bdd5bb
- [x] [T-004] prevent summarize segfault by avoiding eager embedding load | commit: e867da8
- [x] [T-005] fix qdrant probe import mismatch in openrouter branch | commit: pending

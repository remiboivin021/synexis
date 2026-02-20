# TODO — <feature-name>

Branch: feature/<slug>
Worktree: /tmp/wt-<slug>
Owner: $coder
Constitutional ref: `.agents/_constitution.md § 3, § 4`

---

# Rules (Read Before Any Action)

1. Exactly **ONE** active item in `# Current Task` at all times.
2. Active item format is mandatory: `- [ ] [T-NNN] <imperative task description>`
3. Complete current task → commit → move to Done → promote next. This order is non-negotiable.
4. Every commit must follow Conventional Commits with `Task: T-NNN` trailer.
5. Any commit touching `synexis_brain/`, `tests/`, or `docs/` MUST stage this TODO file.
6. `Done` lines must end with `| commit: <short-SHA>`. `commit: pending` must never remain after the commit.
7. Do NOT invent tasks. Tasks come from the planner's execution plan in STATE.

---

# Current Task
- [ ] (none)

---

# Next Tasks
- [ ] [T-001] <next deterministic task>

---

# Blocked
- [ ] [T-xxx] <blocked task> | reason: <reason> | needs: <planner|architect|security>

---

# Done
- [x] [T-000] <bootstrap> | commit: abc1234

# Conventional Commit Quick Reference

```
<type>(<scope>): <imperative description ≤72 chars>

[why — optional body]

Task: T-NNN
Co-authored-by: coder-agent
```

| Type | Use case |
|------|----------|
| `feat` | New behavior |
| `fix` | Bug correction |
| `test` | Tests only |
| `docs` | Docs only |
| `refactor` | Approved refactor |
| `perf` | Performance |
| `chore` | Tooling/config |
| `ci` | CI only |
| `revert` | Undo commit |
| `security` | Security fix |

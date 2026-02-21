# TODO — Web UI Interaction

Branch: feature/web-ui
Worktree: /tmp/wt-web-ui
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
- [ ] (none)

---

# Next Tasks
- [ ] (none)

---

# Blocked
- [ ] [T-xxx] <blocked task> | reason: <reason> | needs: <planner|architect|security>

---

# Done
- [x] [T-000] initialize feature worktree and planning artifacts | commit: 83ed5ce
- [x] [T-001] implement local web server module and CLI command for search/synthesis/document browsing | commit: 83ed5ce
- [x] [T-002] add targeted tests for web safety and helper behavior | commit: 6473be9
- [x] [T-003] update README and add ADR for local web HTTP surface | commit: d8e697f
- [x] [T-004] fix packaged schema loading for web/runtime installs | commit: 3dd8039
- [x] [T-005] make web search bm25-only by default and gate hybrid explicitly | commit: 0524fd1
- [x] [T-006] add markdown rendering in web document viewer with safe html output | commit: 1735a13

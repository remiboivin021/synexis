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
- [x] [T-007] render markdown-formatted synthesis in left web panel with safe html | commit: 4323c2d
- [x] [T-008] refactor web backend from stdlib server to FastAPI while keeping existing API behavior | commit: 803b9ef
- [x] [T-009] fix fastapi request typing causing 422 on /api/search and add regression test | commit: 03bfdc8
- [x] [T-010] split web ui into separate html css js assets and serve them via fastapi | commit: 330f71b
- [x] [T-011] clean fastapi static serving with mounted staticfiles and file response index | commit: f1505f3
- [x] [T-012] wire redesigned index template to real api data and remove mock frontend script | commit: a7f659b
- [x] [T-013] render synthesis markdown in redesigned template using summary_html | commit: 566e4e1
- [x] [T-014] animate synthesis markdown progressive reveal for a more professional reading experience | commit: 0d99fa5
- [x] [T-015] switch synthesis animation to word-by-word markdown rendering | commit: 1119fdd
- [x] [T-016] show backend errors as top-right red toast sliding from right to left | commit: d285c1c
- [x] [T-017] simplify backend error messages to concise one-line user-friendly labels | commit: d094bf1
- [x] [T-018] normalize malformed backend status strings like 402 and map to concise label | commit: 8b15717
- [x] [T-019] display backend errors only in top-right toast and nowhere inline | commit: 2372e13
- [x] [T-020] remove remaining default template values and drive document panel from backend data | commit: 20b9de4
- [x] [T-021] integrate side panel template and bind it to document api data | commit: 7327e64
- [x] [T-022] restore dashboard/search tabs template and hydrate dashboard with backend data | commit: 47ca754
- [x] [T-023] replace template placeholder data with backend-driven values without changing layout blocks | commit: d96f48b
- [x] [T-024] build vault tabs dynamically from configured vault roots and bind filtering | commit: 6586386

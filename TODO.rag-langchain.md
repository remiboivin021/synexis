# TODO — RAG LangChain Service

Branch: feature/rag-langchain
Worktree: /home/comeg/workspace/synexis_brain/wt-rag-langchain
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
- [x] [T-000] initialize rag feature state and execution artifacts | commit: 8d6e461
- [x] [T-001] implement rag package core modules and cli according to rag.nlspec | commit: d22b3c9
- [x] [T-002] add deterministic fixtures and tests for ingestion retrieval generation | commit: 57bf56a
- [x] [T-003] wire packaging env scripts and docs for rag quickstart | commit: c69101e
- [x] [T-004] add low-relevance retrieval guard to return unknown when query has no lexical support | commit: pending

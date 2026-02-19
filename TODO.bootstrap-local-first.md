# TODO — bootstrap-local-first

Branch: feature/bootstrap-local-first
Worktree: .worktrees/wt-bootstrap
Owner: $coder
Constitutional ref: `.agents/_constitution.md § 3, § 4`

---

# Rules (Read Before Any Action)

1. Exactly **ONE** active item in `# Current Task` at all times.
2. Active item format is mandatory: `- [ ] [T-NNN] <imperative task description>`
3. Complete current task -> commit -> move to Done -> promote next. This order is non-negotiable.
4. Every commit must follow Conventional Commits with `Task: T-NNN` trailer.
5. Any commit touching `synexis_brain/`, `tests/`, or `docs/` MUST stage this TODO file.
6. `Done` lines must end with `| commit: <short-SHA>`.

---

# Current Task
- [ ] [T-005] Implémenter la TUI BM25-only avec preview et actions

---

# Next Tasks
- [ ] [T-006] Ajouter couche vectorielle Qdrant + embeddings + merge hybride

---

# Blocked
- [ ] [T-xxx] <blocked task> | reason: <reason> | needs: <planner|architect|security>

---

# Done
- [x] [T-004] Étendre vers indexation incrémentale SQLite + parse/chunk + BM25 | commit: pending
- [x] [T-003] Nettoyer les artefacts build locaux et figer .gitignore | commit: a9f29e1
- [x] [T-002] Implémenter runner DOT minimal avec trace/stats et test hello | commit: c1d5f59
- [x] [T-001] Créer les fondations docs, ADR socle, constitution canonique | commit: 0a1b479
- [x] [T-000] bootstrap feature artifacts | commit: pending

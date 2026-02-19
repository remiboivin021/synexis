# STATE — bootstrap-local-first

Branch: feature/bootstrap-local-first
Worktree: .worktrees/wt-bootstrap
Planner: codex
Executor: codex

---

# Mission

Bootstraper Synexis Brain avec les fondations documentaires et un moteur DOT minimal exécutable.
Cette tranche couvre uniquement la documentation socle et le runner DOT avec traçage.

---

# Feature Type

- [x] new feature
- [ ] bug fix
- [ ] refactor (approved)
- [ ] performance improvement
- [ ] infrastructure
- [ ] security

---

# Acceptance Criteria

- [ ] Les dossiers `docs/architecture/` et `docs/governance/adr/` existent avec une base lisible.
- [ ] Les ADR socle sont présents: DOT runner, chunking heading, read-only Exocortex, Qdrant, scoring hybride.
- [ ] `docs/governance/constitution.md` existe et est aligné avec les règles agents.
- [ ] Un runner DOT minimal exécute un pipeline `hello` et produit `_trace`, `_stats` et logs structurés.
- [ ] Un test automatisé valide le chemin `hello op`.

---

# Scope Contract

## Allowed Areas

- docs/governance/*
- docs/governance/adr/*
- docs/architecture/*
- synexis_brain/__init__.py
- synexis_brain/pipelines/*
- synexis_brain/indexer/pipeline.py
- tests/test_pipeline_runner.py
- pyproject.toml
- README.md
- STATE.bootstrap-local-first.md
- TODO.bootstrap-local-first.md
- DECISIONS.bootstrap-local-first.md

---

## Forbidden Areas

- .agents/*
- connector runtime implementation
- storage schema implementation SQLite/Tantivy/Qdrant
- scoring/merge behavior implementation beyond ADR specification
- TUI implementation details

---

# Blast Radius Assessment

- [x] localized (single module)
- [ ] multi-module
- [ ] cross-system
- [ ] unknown

---

# Architectural Constraints

Pas de nouveau framework. Parser DOT minimal en Python standard library.
Pas de modification des invariants: chunk_id, scoring, storage restent documentés seulement.

---

# Parallel Safety Check

Aucune autre worktree active sur ce repo. Risque de collision: faible.

---

# Execution Plan (Planner Output)

1. [T-001] Créer les fondations docs + ADR socle + artefacts feature.
2. [T-002] Implémenter runner DOT minimal + pipelines example + test hello.
3. [T-003] Nettoyer les artefacts build locaux (`__pycache__`) et figer `.gitignore`.
4. [T-004] Étendre vers indexation incrémentale SQLite + parse/chunk + BM25.

---

# Security Surface Check

Pas de surface sécurité implémentée dans cette tranche (pas de connecteur réseau actif).

---

# Definition of Done

✔ Foundations docs/ADR lisibles
✔ Runner DOT exécutable avec trace/stats
✔ Test runner passe

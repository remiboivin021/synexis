# DECISIONS — bootstrap-local-first

## Rules
- Log only non-trivial decisions.
- Each decision references one `Task` and one `Commit`.
- Architectural decisions require ADR.

## Decision Log

### [D-001] Scope bootstrap en deux tâches

Context: Repo initial quasi vide; demande globale très large.
Decision: Exécuter une tranche prioritaire (foundations + DOT runner) avec commits atomiques.
Rationale: Maximiser le ROI immédiat sans dérive de scope.
Task: T-001
Commit: 0a1b479
Impact: medium, module
Date: 2026-02-19

### [D-002] Parser DOT minimal sans dépendance externe

Context: bootstrap sans dépendances installées et besoin d'un runner immédiatement testable.
Decision: implémenter un parser DOT restreint (nodes, attrs, edges) avec regex stdlib + TopologicalSorter.
Rationale: réduire la complexité initiale tout en respectant le contrat DAG/op registry.
Task: T-002
Commit: c1d5f59
Impact: medium, module
Date: 2026-02-19

### [D-003] Exclure les artefacts Python compilés du VCS

Context: l'exécution locale des validations a produit des fichiers `.pyc`.
Decision: ajouter `.gitignore` et retirer les caches suivis.
Rationale: éviter le bruit de versioning et les diffs non fonctionnels.
Task: T-003
Commit: a9f29e1
Impact: low, localized
Date: 2026-02-19

### [D-004] BM25 bootstrap via SQLite FTS5 avant Tantivy

Context: besoin d'indexation/recherche utilisable immédiatement dans un repo initial.
Decision: implémenter une couche BM25 transitoire basée sur SQLite FTS5, en gardant l'ADR Tantivy comme cible.
Rationale: livrer l'indexation incrémentale et la purge suppression sans bloquer sur dépendances natives.
Task: T-004
Commit: pending
Impact: medium, module
Date: 2026-02-19

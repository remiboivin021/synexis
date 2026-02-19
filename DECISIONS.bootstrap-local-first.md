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
Commit: a5581ed
Impact: medium, module
Date: 2026-02-19

### [D-005] Séparer backend TUI testable du frontend Textual

Context: besoin d'une TUI rapide avec actions, mais environnement sans dépendances UI garanties.
Decision: implémenter `tui/backend.py` (index/search/open/citation) et garder `tui/app.py` comme couche interface.
Rationale: permet validation automatisée des comportements sans lancer l'UI.
Task: T-005
Commit: 10b5fa3
Impact: medium, module
Date: 2026-02-19

### [D-006] Backend BM25 sélectionnable avec fallback explicite

Context: migration vers Tantivy demandée sans dépendances natives garanties dans tous les environnements.
Decision: introduire un builder de backend BM25 (`tantivy` prioritaire, fallback `sqlite` journalisé).
Rationale: activer Tantivy dès disponibilité tout en gardant le moteur fonctionnel localement.
Task: T-006
Commit: 1e84d45
Impact: medium, module
Date: 2026-02-19

### [D-007] Couche vectorielle avec fallback local déterministe

Context: activation vectorielle demandée mais dépendances externes (Qdrant/SentenceTransformer) potentiellement absentes en local.
Decision: implémenter Qdrant + embeddings avec fallback local (SQLite + embedding hash déterministe) activable via config.
Rationale: conserver un mode opérable et testable tout en préparant l'activation complète en environnement équipé.
Task: T-007
Commit: fedfc57
Impact: high, module
Date: 2026-02-19

### [D-008] Accélérer embeddings par batch + cache transactionnel

Context: indexation trop lente sur vault volumineux.
Decision: encoder les chunks manquants en batch et persister le cache embeddings en une transaction.
Rationale: réduire drastiquement le coût CPU/IO par chunk et rendre l'indexation initiale praticable.
Task: T-009
Commit: pending
Impact: high, module
Date: 2026-02-19

### [D-009] Adapter Tantivy/Qdrant aux APIs runtime observées

Context: bindings Tantivy installés sans `QueryParser`/`Term`, et collection Qdrant non peuplée de façon fiable.
Decision: utiliser `Index.parse_query`, `delete_documents_by_term`, `index.reload()`, et un upsert Qdrant incrémental sans `recreate_collection`.
Rationale: éviter les crashs, conserver les points existants et fiabiliser la présence d'objets côté Qdrant.
Task: T-009
Commit: pending
Impact: high, module
Date: 2026-02-19

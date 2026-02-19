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
Commit: 5ebd2e3
Impact: high, module
Date: 2026-02-19

### [D-009] Adapter Tantivy/Qdrant aux APIs runtime observées

Context: bindings Tantivy installés sans `QueryParser`/`Term`, et collection Qdrant non peuplée de façon fiable.
Decision: utiliser `Index.parse_query`, `delete_documents_by_term`, `index.reload()`, et un upsert Qdrant incrémental sans `recreate_collection`.
Rationale: éviter les crashs, conserver les points existants et fiabiliser la présence d'objets côté Qdrant.
Task: T-009
Commit: 5ebd2e3
Impact: high, module
Date: 2026-02-19

### [D-010] Embedding hash par défaut pour indexation rapide

Context: indexation encore trop longue sur machine locale et grands vaults.
Decision: rendre `vector.embedding_backend=hash` par défaut; `sentence-transformers` devient opt-in explicite.
Rationale: supprimer le coût de chargement/inférence modèle par défaut et garder une expérience réactive.
Task: T-011
Commit: caa1fbf
Impact: medium, module
Date: 2026-02-19

### [D-011] Tolérance mtime pour éviter reindex complet inutile

Context: réindexation observée comme très longue à chaque run même sans modification des fichiers.
Decision: comparer `mtime` avec tolérance epsilon pour absorber le bruit float SQLite.
Rationale: empêcher les faux positifs \"changed\" et rendre les runs successifs quasi instantanés.
Task: T-011
Commit: caa1fbf
Impact: medium, module
Date: 2026-02-19

### [D-012] Résoudre db/index path relatifs sur base du fichier config

Context: indexation perçue comme systématiquement longue malgré absence de changements.
Decision: résoudre `db_path`, `tantivy_index_dir` et chemins vault relatifs par rapport au dossier de `config.yml`.
Rationale: éviter la dérive liée au répertoire courant et empêcher la recréation implicite d'index/meta ailleurs.
Task: T-013
Commit: 10ad1e4
Impact: medium, module
Date: 2026-02-19

### [D-013] Autoriser SQLite pour les appels de reindex en thread

Context: `action_reindex` exécute `service.reindex` dans `asyncio.to_thread`, provoquant une erreur SQLite de thread affinity.
Decision: ouvrir la connexion SQLite avec `check_same_thread=False`.
Rationale: garder l'UI non bloquante sans crash runtime sur reindex.
Task: T-014
Commit: a8c0677
Impact: medium, module
Date: 2026-02-19

### [D-014] Rebuild BM25 si l'index FTS est vide malgré metadata inchangée

Context: recherche vide observée alors que `scan` retourne `unchanged` (metadata déjà indexée).
Decision: forcer une passe de reconstruction quand backend SQLite BM25 est vide.
Rationale: garantir des résultats même après switch backend/config ou corruption partielle de la table FTS.
Task: T-015
Commit: 6ece1b1
Impact: medium, module
Date: 2026-02-19

### [D-015] Normaliser la requête BM25 FTS pour meilleure tolérance FR

Context: requête utilisateur `projets en cours` sans résultat malgré contenu pertinent.
Decision: transformer la requête en clauses FTS avec prefix (`*`) et variante singulier/pluriel simple.
Rationale: augmenter le rappel sans changer l'architecture de recherche.
Task: T-016
Commit: b973dc1
Impact: medium, module
Date: 2026-02-19

### [D-016] NLU heuristique pour filtres implicites de requête

Context: besoin d'inférer des filtres intelligents depuis le langage naturel utilisateur.
Decision: ajouter un parseur léger déterministe (status/type/tag/vault) sans dépendances externes.
Rationale: améliorer la pertinence immédiate des résultats tout en gardant un comportement prévisible.
Task: T-017
Commit: pending
Impact: medium, module
Date: 2026-02-19

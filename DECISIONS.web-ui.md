# DECISIONS — Web UI Interaction

## Rules
- Log only non-trivial decisions.
- Each decision references one `Task` and one `Commit`.
- Architectural decisions require ADR.

## Decision Log

### [D-001] Serveur web natif sans nouvelle dépendance

Context: La feature web nécessite une surface HTTP, mais l'ajout d'un framework introduirait une dépendance et un risque supply-chain supplémentaire.
Decision: Implémenter le serveur et l'API avec `ThreadingHTTPServer` + `BaseHTTPRequestHandler` de la standard library.
Rationale: Diff minimal, dépendances inchangées, et contrôle explicite de l'exposition réseau.
Task: T-001
Commit: 83ed5ce
Impact: medium, module
Date: 2026-02-21

### [D-002] Tests orientés garde-fous réseau et frontière de lecture

Context: Les endpoints de recherche dépendent d'OpenSearch/Qdrant, mais les risques critiques initiaux concernent l'exposition réseau et la lecture de fichiers hors roots.
Decision: Ajouter des tests unitaires ciblés sur `resolve_bind_host`, `_is_under_roots` et `_read_doc_content`.
Rationale: Couvrir rapidement les invariants de sécurité locale sans rendre la suite dépendante des backends externes.
Task: T-002
Commit: pending
Impact: low, localized
Date: 2026-02-21

### [D-003] Formaliser la surface web en ADR dédiée

Context: L'interface web introduit un nouvel accès HTTP, donc une extension explicite de la surface d'interaction.
Decision: Ajouter une ADR dédiée décrivant portée, contraintes de bind local, alternatives et rollback.
Rationale: Maintenir la traçabilité architecturale et clarifier la posture sécurité avant merge.
Task: T-003
Commit: pending
Impact: medium, module
Date: 2026-02-21

### [D-004] Charger schema SQL depuis package_data en mode installé

Context: L'exécution depuis `site-packages` échouait car `schema.sql` n'était pas embarqué, cassant `MetadataDB.init_schema()`.
Decision: Déclarer `searchctl.metadata/schema.sql` dans `tool.setuptools.package-data` et ajouter un chargement robuste via `importlib.resources`.
Rationale: Le runtime fonctionne à la fois en source tree et en installation wheel/editable.
Task: T-004
Commit: pending
Impact: medium, localized
Date: 2026-02-21

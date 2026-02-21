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
Commit: 6473be9
Impact: low, localized
Date: 2026-02-21

### [D-003] Formaliser la surface web en ADR dédiée

Context: L'interface web introduit un nouvel accès HTTP, donc une extension explicite de la surface d'interaction.
Decision: Ajouter une ADR dédiée décrivant portée, contraintes de bind local, alternatives et rollback.
Rationale: Maintenir la traçabilité architecturale et clarifier la posture sécurité avant merge.
Task: T-003
Commit: d8e697f
Impact: medium, module
Date: 2026-02-21

### [D-004] Charger schema SQL depuis package_data en mode installé

Context: L'exécution depuis `site-packages` échouait car `schema.sql` n'était pas embarqué, cassant `MetadataDB.init_schema()`.
Decision: Déclarer `searchctl.metadata/schema.sql` dans `tool.setuptools.package-data` et ajouter un chargement robuste via `importlib.resources`.
Rationale: Le runtime fonctionne à la fois en source tree et en installation wheel/editable.
Task: T-004
Commit: 3dd8039
Impact: medium, localized
Date: 2026-02-21

### [D-005] Web en BM25-only par défaut pour éviter crash embeddings

Context: Des segfaults surviennent lors des requêtes web en chemin hybride (embeddings + qdrant runtime), bloquant l'usage.
Decision: Basculer la recherche web en BM25-only par défaut, avec activation explicite de l'hybride (checkbox UI / flag CLI).
Rationale: Réduire le risque runtime par défaut tout en conservant la capacité hybride à la demande.
Task: T-005
Commit: 0524fd1
Impact: medium, localized
Date: 2026-02-21

### [D-006] Rendu Markdown serveur avec échappement HTML strict

Context: L'affichage brut du Markdown dans la web UI était peu lisible.
Decision: Ajouter un rendu Markdown minimal côté serveur (titres/listes/code/inline) avec échappement HTML systématique.
Rationale: Améliorer la lisibilité sans ajouter de dépendance runtime ni ouvrir une surface XSS par injection HTML brute.
Task: T-006
Commit: pending
Impact: medium, localized
Date: 2026-02-21

### [D-007] Rendu Markdown aussi pour la synthèse de gauche

Context: La synthèse OpenRouter pouvait contenir du Markdown mais était affichée en texte brut dans la colonne gauche.
Decision: Ajouter `summary_html` dans la réponse API et l'afficher en `innerHTML` via le renderer Markdown sécurisé existant.
Rationale: Cohérence visuelle avec la lecture document, sans élargir la surface de risque XSS.
Task: T-007
Commit: pending
Impact: low, localized
Date: 2026-02-21

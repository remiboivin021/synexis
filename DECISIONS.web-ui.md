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
Commit: 1735a13
Impact: medium, localized
Date: 2026-02-21

### [D-007] Rendu Markdown aussi pour la synthèse de gauche

Context: La synthèse OpenRouter pouvait contenir du Markdown mais était affichée en texte brut dans la colonne gauche.
Decision: Ajouter `summary_html` dans la réponse API et l'afficher en `innerHTML` via le renderer Markdown sécurisé existant.
Rationale: Cohérence visuelle avec la lecture document, sans élargir la surface de risque XSS.
Task: T-007
Commit: 4323c2d
Impact: low, localized
Date: 2026-02-21

### [D-008] Migrer le serveur web vers FastAPI/Uvicorn

Context: La surface web grandit (rendu markdown, synthèse, API JSON) et `http.server` devient moins maintenable.
Decision: Remplacer le serveur stdlib par une app FastAPI + exécution Uvicorn en conservant les mêmes routes et contrats JSON.
Rationale: Routage/maintenance plus robustes avec un diff limité et sans changement du comportement métier search/summarize.
Task: T-008
Commit: 803b9ef
Impact: medium, module
Date: 2026-02-21

### [D-009] Importer Request au niveau module pour éviter 422 FastAPI

Context: `POST /api/search` renvoyait 422 car l'annotation `Request` (import local dans `create_app`) n'était pas résolue avec annotations différées.
Decision: Importer `FastAPI`, `Request`, `HTMLResponse`, `JSONResponse` au niveau module et ajouter un test de non-régression endpoint.
Rationale: Rétablir l'injection correcte de `Request` par FastAPI et stabiliser le contrat API.
Task: T-009
Commit: 03bfdc8
Impact: low, localized
Date: 2026-02-21

### [D-010] Extraire UI web dans des assets dédiés

Context: L'UI était inline dans `web.py`, ce qui compliquait les itérations front et la lisibilité.
Decision: Déplacer le frontend en fichiers séparés (`src/searchctl/assets/index.html`, `src/searchctl/assets/app.css`, `src/searchctl/assets/app.js`) servis par FastAPI.
Rationale: Séparation claire backend/frontend avec contrats API inchangés.
Task: T-010
Commit: 330f71b
Impact: low, localized
Date: 2026-02-21

### [D-011] Servir les assets avec StaticFiles plutôt que routes manuelles

Context: Les routes manuelles `/static/app.css` et `/static/app.js` alourdissaient `web.py`.
Decision: Monter le dossier assets avec `app.mount('/static', StaticFiles(...))` et servir `/` via `FileResponse(index.html)`.
Rationale: Implémentation FastAPI plus idiomatique, moins de code serveur et maintenance plus simple.
Task: T-011
Commit: f1505f3
Impact: low, localized
Date: 2026-02-21

### [D-012] Brancher le template redesign sur les vraies APIs et supprimer les mocks

Context: Le nouveau `index.html` contenait un script inline avec des données simulées, déconnecté des endpoints backend.
Decision: Retirer le script mock dans `index.html` et adapter `app.js` aux IDs du nouveau design pour consommer `/api/documents` et `/api/search`.
Rationale: Préserver le design fourni tout en reconnectant l'UI à la donnée réelle du moteur.
Task: T-012
Commit: a7f659b
Impact: low, localized
Date: 2026-02-21

### [D-013] Afficher la synthèse en markdown rendu dans le template redesign

Context: La vue synthèse du nouveau template affichait encore du texte brut avec effet typewriter.
Decision: Utiliser prioritairement `summary_html` (rendu markdown serveur) dans `#synthesis-text`, avec fallback typewriter sur `summary`.
Rationale: Cohérence avec la capacité markdown déjà exposée par l'API et meilleure lisibilité.
Task: T-013
Commit: 566e4e1
Impact: low, localized
Date: 2026-02-21

### [D-014] Animer l'affichage progressif de la synthèse Markdown

Context: La synthèse markdown s'affichait instantanément, ce qui rendait l'expérience moins fluide visuellement.
Decision: Révéler progressivement les blocs HTML de `summary_html` (et les items de listes) avec une animation fade/slide courte.
Rationale: Donner un ressenti plus "live" et professionnel tout en conservant le rendu Markdown déjà sécurisé côté serveur.
Task: T-014
Commit: 0d99fa5
Impact: low, localized
Date: 2026-02-21

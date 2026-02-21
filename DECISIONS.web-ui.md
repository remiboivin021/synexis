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
Commit: pending
Impact: medium, module
Date: 2026-02-21

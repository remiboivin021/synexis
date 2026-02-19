# ADR 0004: Qdrant vector store

- Date: 2026-02-19
- Status: Accepted
- Décideur: architect

## Contexte
La recherche sémantique nécessite un store vectoriel local avec filtrage payload.

## Décision
Qdrant est retenu comme store vectoriel local (docker-compose), avec `chunk_id` comme clé logique.

## Conséquences
- Positives: bonne ergonomie locale, filtres payload robustes.
- Négatives: composant runtime additionnel.

## Alternatives considérées
- FAISS brut: rejeté (gestion payload/ops plus lourde).
- Chroma: rejeté (moins aligné avec contraintes prévues).

## Invariants impactés
- I-04: pas d'orphelins.
- I-10: comportement déterministe.

## Migration plan (si applicable)
Documenter collection schema à l'introduction effective.

## Rollback plan (si applicable)
Mode BM25-only en désactivant la couche vectorielle.

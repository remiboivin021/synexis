# ADR 0005: Hybrid scoring policy

- Date: 2026-02-19
- Status: Accepted
- Décideur: architect

## Contexte
Synexis combine BM25 et vecteur; le merge doit être stable et explicable.

## Décision
La politique hybride suit une formule pondérée normalisée par source, avec paramètres versionnés.
Toute modification de poids/rerank exige évaluation mesurable + ADR.

## Conséquences
- Positives: réglages traçables et contrôlés.
- Négatives: tuning nécessite discipline d'évaluation.

## Alternatives considérées
- Rerank heuristique ad hoc: rejeté (non gouvernable).

## Invariants impactés
- I-05: scoring non modifiable sans ADR.

## Migration plan (si applicable)
Versionner les paramètres et fournir backward defaults.

## Rollback plan (si applicable)
Revenir à la version précédente de la policy.

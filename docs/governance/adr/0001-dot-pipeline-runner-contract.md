# ADR 0001: DOT pipeline + runner contract

- Date: 2026-02-19
- Status: Accepted
- Décideur: architect

## Contexte
Synexis doit rester déterministe et local-first. L'orchestration doit rester explicite et auditables.

## Décision
Les pipelines sont définis en DOT (`digraph`) et exécutés uniquement par un runner DAG minimal.
Chaque nœud porte un `op` résolu par registry `op -> fn`.
Le runner produit `_trace` et `_stats` pour chaque exécution.

## Conséquences
- Positives: orchestration lisible, testable, stable.
- Négatives: parser DOT volontairement restreint.

## Alternatives considérées
- YAML pipelines: rejeté (moins standard pour graphes).
- Orchestration implicite Python: rejeté (drift non visible).

## Invariants impactés
- I-06: Pipelines DOT comme source de vérité.
- I-10: Déterminisme d'exécution.

## Migration plan (si applicable)
N/A (nouveau socle).

## Rollback plan (si applicable)
Revenir à la version antérieure sans runner.

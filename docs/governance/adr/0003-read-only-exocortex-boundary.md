# ADR 0003: Read-only boundary Exocortex

- Date: 2026-02-19
- Status: Accepted
- Décideur: architect

## Contexte
Synexis indexe des vaults externes qui restent la source de vérité.

## Décision
Les vaults Exocortex sont strictement read-only par défaut.
Aucune mutation silencieuse; toute écriture nécessite action explicite utilisateur.

## Conséquences
- Positives: confiance et sécurité des données source.
- Négatives: certaines automatisations sont volontairement interdites.

## Alternatives considérées
- Auto-fix/auto-write: rejeté (viol de confiance).

## Invariants impactés
- I-08: TUI non mutante.
- I-09: connecteurs explicites.

## Migration plan (si applicable)
N/A.

## Rollback plan (si applicable)
N/A.

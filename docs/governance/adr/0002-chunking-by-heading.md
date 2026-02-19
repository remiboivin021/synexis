# ADR 0002: Chunking by heading

- Date: 2026-02-19
- Status: Accepted
- Décideur: architect

## Contexte
Les notes Markdown sont structurées par headings; il faut des chunks stables et explicables.

## Décision
Le chunking se fait par section de heading Markdown; chaque chunk conserve path, heading et texte.
`chunk_id` reste déterministe selon le contrat AGENTS.

## Conséquences
- Positives: citations lisibles, mapping note->chunk explicite.
- Négatives: granularité dépend de la qualité des headings.

## Alternatives considérées
- Chunk fixe par tokens: rejeté (moins interprétable).
- Chunk par paragraphe: rejeté (bruit plus élevé).

## Invariants impactés
- I-01: Identité chunk déterministe.

## Migration plan (si applicable)
N/A au bootstrap.

## Rollback plan (si applicable)
N/A au bootstrap.

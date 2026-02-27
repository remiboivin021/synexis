from __future__ import annotations

import json
from typing import Any


SUMMARY_SYSTEM_PROMPT = (
    "Tu es un assistant de synthese documentaire. "
    "Redige une synthese claire, concise, orientee action, en francais. "
    "N'invente aucun fait. Base-toi uniquement sur les extraits fournis."
)


def build_summary_user_prompt(query: str, results: list[dict[str, Any]], strict_grounding: bool = False) -> str:
    source_policy = (
        "Chaque affirmation factuelle doit inclure une citation inline au format [Sx] "
        "en utilisant exclusivement les source_id fournis. "
        "Si les extraits ne suffisent pas, reponds uniquement: "
        "\"Information insuffisante dans les sources fournies.\""
        if strict_grounding
        else "Ne pas citer de source inline. Les sources seront ajoutees apres la synthese."
    )
    payload = {
        "query": query,
        "results": results,
        "instructions": {
            "style": "lisible humain, phrases courtes, structure en sections",
            "required_sections": [
                "Synthese",
                "Points cles",
                "Actions recommandees",
            ],
            "source_policy": source_policy,
        },
    }
    return (
        "Produis une synthese des resultats de recherche ci-dessous. "
        "Reste factuel et utile pour la decision.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )

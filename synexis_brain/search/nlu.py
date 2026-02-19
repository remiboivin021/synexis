from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class InferredFilters:
    vault_id: str = ""
    chunk_type: str = ""
    tag: str = ""
    status: str = ""


@dataclass
class NLUQuery:
    text_query: str
    inferred: InferredFilters


_STATUS_KEYWORDS = {
    "open": {"open", "todo", "to-do", "en", "cours", "ongoing", "active", "actif", "encours"},
    "done": {
        "done",
        "closed",
        "complete",
        "completed",
        "termine",
        "terminee",
        "terminé",
        "terminée",
        "fini",
        "archive",
        "archivé",
    },
}

_TYPE_KEYWORDS = {
    "playbook": {"playbook", "playbooks", "runbook", "runbooks"},
    "decision": {"decision", "decisions", "décision", "décisions", "adr"},
}


def infer_filters(query: str, available_vaults: list[str]) -> NLUQuery:
    raw = query.strip()
    if not raw:
        return NLUQuery(text_query="", inferred=InferredFilters())

    lowered = raw.lower()
    tokens = re.findall(r"[a-zA-Z0-9_#:-]+", lowered)

    inferred = InferredFilters()
    consumed = set()

    for idx, token in enumerate(tokens):
        if token.startswith("tag:"):
            inferred.tag = token.split(":", 1)[1]
            consumed.add(idx)
        elif token.startswith("#") and len(token) > 1:
            inferred.tag = token[1:]
            consumed.add(idx)

    for normalized, kws in _TYPE_KEYWORDS.items():
        for idx, token in enumerate(tokens):
            if token in kws and not inferred.chunk_type:
                inferred.chunk_type = normalized
                consumed.add(idx)

    for normalized, kws in _STATUS_KEYWORDS.items():
        for idx, token in enumerate(tokens):
            if token in kws and not inferred.status:
                inferred.status = normalized
                consumed.add(idx)

    for vault in available_vaults:
        v = vault.lower()
        for idx, token in enumerate(tokens):
            if token == v or token in v or v in token:
                inferred.vault_id = vault
                consumed.add(idx)

    remaining = [tok for i, tok in enumerate(tokens) if i not in consumed and not tok.startswith("tag:") and not tok.startswith("#")]
    cleaned = " ".join(remaining).strip()
    return NLUQuery(text_query=cleaned or raw, inferred=inferred)

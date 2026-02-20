from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def normalize_text(text: str) -> str:
    base = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return base.lower()


def infer_scope(path: str) -> str:
    p = normalize_text(path)
    if "/03_projects/" in p:
        return "projects"
    if "/05_playbooks/" in p:
        return "playbooks"
    if "/04_decisions/" in p:
        return "decisions"
    if "/90_dashboard/" in p:
        return "dashboard"
    if "/02_knowledge/" in p:
        return "knowledge"
    return "other"


def infer_active(title: str, text: str, path: str) -> bool:
    body = normalize_text(" ".join([title, text[:4000], path]))
    active_markers = [
        "en cours",
        "actif",
        "active",
        "current",
        "ongoing",
        "projets actifs",
        "projet actif",
        "focus actuel",
    ]
    if any(mark in body for mark in active_markers):
        return True
    # Files under a current project subtree are considered active by default.
    return infer_scope(path) == "projects" and any(m in body for m in ["outcome vise", "jalons", "milestone", "prochaines etapes"])


def classify_document(path: str, title: str, text: str) -> dict[str, Any]:
    scope = infer_scope(path)
    active = infer_active(title, text, path)
    tags = sorted(set(re.findall(r"#[a-zA-Z0-9_/-]+", text)))[:32]
    return {
        "path": path,
        "title": title,
        "scope": scope,
        "active": active,
        "tags": tags,
    }


def write_document_map(entries: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    entries_sorted = sorted(entries, key=lambda e: (e.get("scope", ""), e.get("path", "")))
    output_path.write_text(json.dumps(entries_sorted, ensure_ascii=False, indent=2), encoding="utf-8")

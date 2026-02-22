from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path


@dataclass(slots=True)
class ManifestDoc:
    hash: str
    num_chunks: int
    sources: list[str]
    ingested_at: str


def manifest_path(persist_dir: Path) -> Path:
    return persist_dir / "manifest.json"


def load_manifest(persist_dir: Path) -> dict[str, dict]:
    path = manifest_path(persist_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(persist_dir: Path, manifest: dict[str, dict]) -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    manifest_path(persist_dir).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def compute_doc_hash(text: str) -> str:
    return sha1(text.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

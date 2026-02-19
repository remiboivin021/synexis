from __future__ import annotations

from datetime import datetime, timezone
import fnmatch
import hashlib
from pathlib import Path
from typing import Any

from synexis_brain.config import load_config
from synexis_brain.indexer.metadata import ensure_meta_tables, get_file_meta, list_file_meta


def _mtime_changed(stored_mtime: float, current_mtime: float) -> bool:
    # SQLite float round-trips can drift by tiny epsilons; keep scan deterministic.
    return abs(stored_mtime - current_mtime) > 1e-6


def _sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _matches(rel_path: str, includes: list[str], excludes: list[str]) -> bool:
    def match_any(patterns: list[str]) -> bool:
        for pat in patterns:
            if fnmatch.fnmatch(rel_path, pat):
                return True
            if pat.startswith("**/") and fnmatch.fnmatch(rel_path, pat[3:]):
                return True
        return False

    included = match_any(includes)
    excluded = match_any(excludes)
    return included and not excluded


def scan_vaults(context: dict[str, Any], params: dict[str, str]) -> dict[str, Any]:
    config_path = params.get("config_path") or context.get("config_path")
    if not config_path:
        raise ValueError("config_path is required")

    config = load_config(config_path)
    db_path = params.get("db_path") or context.get("db_path")
    if not db_path:
        raise ValueError("db_path is required")

    conn = context["db_conn"]
    ensure_meta_tables(conn)

    seen: set[tuple[str, str]] = set()
    scan_items: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()

    for vault in config.get("vaults", []):
        vault_id = str(vault["id"])
        vault_path = Path(str(vault["path"]))
        includes = list(vault.get("include", ["**/*.md"]))
        excludes = list(vault.get("exclude", []))

        for md_file in vault_path.rglob("*.md"):
            rel_path = md_file.relative_to(vault_path).as_posix()
            if not _matches(rel_path, includes, excludes):
                continue
            stat = md_file.stat()
            meta = get_file_meta(conn, vault_id, rel_path)
            file_hash = meta["file_hash"] if meta else ""
            action = "unchanged"

            if not meta:
                action = "new"
                file_hash = _sha1_file(md_file)
            elif _mtime_changed(float(meta["mtime"]), float(stat.st_mtime)) or int(meta["size"]) != stat.st_size:
                new_hash = _sha1_file(md_file)
                if new_hash != meta["file_hash"]:
                    action = "changed"
                file_hash = new_hash

            seen.add((vault_id, rel_path))
            scan_items.append(
                {
                    "action": action,
                    "vault_id": vault_id,
                    "vault_path": str(vault_path),
                    "path": rel_path,
                    "abs_path": str(md_file),
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "file_hash": file_hash,
                    "last_indexed": now,
                }
            )

    known = {(row["vault_id"], row["path"]) for row in list_file_meta(conn)}
    deleted = sorted(known - seen)

    return {
        "config": config,
        "scan_items": scan_items,
        "changes": {
            "new": sum(1 for i in scan_items if i["action"] == "new"),
            "changed": sum(1 for i in scan_items if i["action"] == "changed"),
            "unchanged": sum(1 for i in scan_items if i["action"] == "unchanged"),
            "deleted": [{"vault_id": v, "path": p} for v, p in deleted],
        },
    }

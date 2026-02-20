from __future__ import annotations

from pathlib import Path


def discover_files(roots: list[str], include_extensions: list[str], exclude_globs: list[str]) -> list[Path]:
    include = {ext.lower() for ext in include_extensions}
    found: list[Path] = []
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in include:
                continue
            posix = path.as_posix()
            if any(path.match(p) or posix.endswith(p.replace("**/", "")) for p in exclude_globs):
                continue
            found.append(path.resolve())
    return sorted(found)

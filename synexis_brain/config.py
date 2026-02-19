from __future__ import annotations

from pathlib import Path
from typing import Any


def _fallback_parse_config(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {"vaults": []}
    current_vault: dict[str, Any] | None = None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            current_vault = {}
            data["vaults"].append(current_vault)
            stripped = stripped[2:].strip()
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current_vault[key.strip()] = value.strip().strip('"').strip("'")
            continue
        if ":" in stripped and current_vault is not None:
            key, value = stripped.split(":", 1)
            val = value.strip()
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",") if x.strip()]
                current_vault[key.strip()] = items
            else:
                current_vault[key.strip()] = val.strip('"').strip("'")
    return data


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    raw = config_path.read_text(encoding="utf-8")

    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        data = _fallback_parse_config(raw)
    else:
        data = yaml.safe_load(raw) or {}

    if not isinstance(data, dict):
        raise ValueError("config.yaml root must be a mapping")
    data.setdefault("vaults", [])
    return data

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from searchctl.prompts import SUMMARY_SYSTEM_PROMPT


@dataclass
class OpenRouterConfig:
    base_url: str
    model: str
    api_key: str
    app_name: str = "searchctl"


def build_openrouter_payload(model: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 700) -> dict[str, Any]:
    return {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }


def _extract_content(resp: dict[str, Any]) -> str:
    choices = resp.get("choices") or []
    if not choices:
        raise RuntimeError("OpenRouter response has no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise RuntimeError("OpenRouter response content is empty")
    return str(content).strip()


def call_openrouter_summary(cfg: OpenRouterConfig, user_prompt: str) -> str:
    api_key = cfg.api_key or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing (set env var or config.llm.api_key)")

    body = build_openrouter_payload(cfg.model, user_prompt)
    data = json.dumps(body).encode("utf-8")
    req = Request(
        url=cfg.base_url.rstrip("/") + "/chat/completions",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://local.searchctl",
            "X-Title": cfg.app_name,
        },
    )

    try:
        with urlopen(req, timeout=60) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenRouter network error: {exc}") from exc

    return _extract_content(parsed)

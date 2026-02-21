from __future__ import annotations

import json
import re
import unicodedata
from html import escape
from importlib import resources
from pathlib import Path
from typing import Any

from opensearchpy.exceptions import NotFoundError
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from searchctl.config import AppConfig, load_config
from searchctl.document_map import infer_scope, map_boost
from searchctl.fusion import rrf_fuse
from searchctl.llm_openrouter import OpenRouterConfig, call_openrouter_summary
from searchctl.metadata.db import MetadataDB
from searchctl.opensearch.client import make_client as make_opensearch_client
from searchctl.opensearch.queries import bm25_search
from searchctl.prompts import build_summary_user_prompt
from searchctl.qdrant.client import make_client as make_qdrant_client
from searchctl.qdrant.queries import vector_search
from searchctl.snippets import build_snippet
from searchctl.summary import collect_sources, summary_input_rows

STOPWORDS_FR = {"de", "des", "du", "la", "le", "les", "un", "une", "et", "en", "dans", "sur", "pour", "au", "aux"}
DEFAULT_HOST = "127.0.0.1"
MAX_BODY_BYTES = 64_000


def resolve_bind_host(host: str, allow_remote: bool) -> str:
    normalized = host.strip() if host else DEFAULT_HOST
    local_hosts = {"127.0.0.1", "localhost", "::1"}
    if normalized in local_hosts:
        return normalized
    if allow_remote:
        return normalized
    raise ValueError("remote bind denied; pass --allow-remote explicitly")


def should_use_vector(use_hybrid: bool, summarize: bool, summary_use_hybrid: bool) -> bool:
    return use_hybrid or (summarize and summary_use_hybrid)


def _normalize_text(text: str) -> str:
    no_accents = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return no_accents.lower()


def _query_terms(query: str) -> list[str]:
    terms = []
    for raw in _normalize_text(query).replace('"', " ").replace("'", " ").split():
        token = raw.strip(".,:;!?()[]{}")
        if len(token) < 3 or token in STOPWORDS_FR:
            continue
        terms.append(token)
    return terms


def _matches_terms(payload: dict[str, Any], required_terms: list[str]) -> bool:
    if not required_terms:
        return True
    haystack = _normalize_text(
        " ".join(
            [
                str(payload.get("title") or ""),
                str(payload.get("path") or ""),
                str(payload.get("text") or ""),
            ]
        )
    )
    words = set(re.findall(r"[a-z0-9_]+", haystack))
    return all(term in words for term in required_terms)


def _project_intent_guard(query: str, payload: dict[str, Any]) -> bool:
    q = _normalize_text(query)
    wants_project = "projet" in q or "project" in q
    wants_active = ("en cours" in q) or ("actif" in q) or ("active" in q) or ("current" in q)
    if not (wants_project and wants_active):
        return True
    title = _normalize_text(str(payload.get("title") or ""))
    path = _normalize_text(str(payload.get("path") or ""))
    text = _normalize_text(str(payload.get("text") or ""))
    is_project_doc = ("03_projects" in path) or ("project" in title) or ("projet" in title)
    is_active_doc = ("en cours" in text) or ("actif" in text) or ("active" in text) or ("current" in text)
    return is_project_doc and is_active_doc


def _summarize_with_openrouter(query: str, rows: list[dict[str, Any]], cfg: AppConfig, top_n: int) -> str:
    summary_input = summary_input_rows(rows, top_n)
    prompt = build_summary_user_prompt(query, summary_input)
    llm_cfg = OpenRouterConfig(
        base_url=cfg.llm.base_url,
        model=cfg.llm.model,
        api_key=cfg.llm.api_key,
        app_name="searchctl-web",
    )
    return call_openrouter_summary(llm_cfg, prompt)


def _is_under_roots(path: Path, roots: list[str]) -> bool:
    resolved = path.resolve()
    for root in roots:
        root_path = Path(root).resolve()
        if resolved == root_path or root_path in resolved.parents:
            return True
    return False


def _read_doc_content(doc: dict[str, Any], cfg: AppConfig) -> str:
    source_type = str(doc.get("source_type") or "")
    doc_id = str(doc.get("doc_id") or "")
    path = Path(str(doc.get("path") or "")).resolve()
    if not _is_under_roots(path, cfg.roots):
        raise PermissionError("document path outside configured roots")

    if source_type == "pdf":
        cache_path = Path(cfg.metadata.extracted_text_cache_dir) / f"{doc_id}.txt"
        if not cache_path.exists():
            raise FileNotFoundError("cached extracted text not found for pdf")
        return cache_path.read_text(encoding="utf-8")

    return path.read_text(encoding="utf-8", errors="replace")


def _inline_markdown(text: str) -> str:
    out = escape(text, quote=False)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return out


def render_markdown_safe(text: str) -> str:
    lines = text.splitlines()
    html_parts: list[str] = []
    in_code = False
    in_list = False
    code_lines: list[str] = []

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                html_parts.append("<pre><code>" + escape("\n".join(code_lines), quote=False) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                if in_list:
                    html_parts.append("</ul>")
                    in_list = False
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        if stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append("<li>" + _inline_markdown(stripped[2:]) + "</li>")
            continue

        if in_list:
            html_parts.append("</ul>")
            in_list = False

        if stripped.startswith("### "):
            html_parts.append("<h3>" + _inline_markdown(stripped[4:]) + "</h3>")
        elif stripped.startswith("## "):
            html_parts.append("<h2>" + _inline_markdown(stripped[3:]) + "</h2>")
        elif stripped.startswith("# "):
            html_parts.append("<h1>" + _inline_markdown(stripped[2:]) + "</h1>")
        else:
            html_parts.append("<p>" + _inline_markdown(stripped) + "</p>")

    if in_list:
        html_parts.append("</ul>")
    if in_code:
        html_parts.append("<pre><code>" + escape("\n".join(code_lines), quote=False) + "</code></pre>")

    return "\n".join(html_parts)


def _load_asset_text(filename: str) -> str:
    asset_path = Path(__file__).with_name("assets") / filename
    if asset_path.exists():
        return asset_path.read_text(encoding="utf-8")
    try:
        return resources.files("searchctl").joinpath("assets").joinpath(filename).read_text(encoding="utf-8")
    except Exception as exc:
        raise FileNotFoundError(f"web asset not found: {filename}") from exc


def _search_rows(
    cfg: AppConfig,
    query: str,
    top: int | None,
    summarize: bool,
    summary_top_k: int,
    use_hybrid: bool,
    summary_use_hybrid: bool,
    strict: bool,
) -> dict[str, Any]:
    os_client = make_opensearch_client(cfg.opensearch.url)
    use_vector = should_use_vector(use_hybrid, summarize, summary_use_hybrid)
    q_client = make_qdrant_client(cfg.qdrant.url) if use_vector else None

    try:
        bm25 = bm25_search(
            os_client,
            cfg.opensearch.index_name,
            query,
            cfg.search.bm25_top_k,
            None,
            None,
        )
    except NotFoundError as exc:
        if getattr(exc, "error", "") == "index_not_found_exception":
            raise RuntimeError(
                f"OpenSearch index '{cfg.opensearch.index_name}' not found. Run ingest before web search."
            ) from exc
        raise

    if use_vector:
        from searchctl.embeddings import Embedder

        embedder = Embedder(cfg.embeddings.model_name, cfg.embeddings.device)
        qvec = embedder.encode_query(query).tolist()
        vec = vector_search(
            q_client,
            cfg.qdrant.collection_name,
            qvec,
            cfg.search.vector_top_k,
            None,
            None,
        )
    else:
        vec = []

    fused = rrf_fuse(bm25, vec, cfg.search.rrf_k)
    boosted_rows = [(row, row.score + map_boost(row.payload, query)) for row in fused]
    boosted_rows.sort(
        key=lambda item: (
            -item[1],
            item[0].bm25_rank if item[0].bm25_rank is not None else 10**9,
            item[0].vector_rank if item[0].vector_rank is not None else 10**9,
            item[0].chunk_id,
        )
    )

    limit = top or cfg.search.return_top_n
    strict_terms = _query_terms(query) if strict else []
    result_rows: list[dict[str, Any]] = []

    for rank, (row, effective_score) in enumerate(boosted_rows, start=1):
        payload = row.payload
        if not _matches_terms(payload, strict_terms):
            continue
        if strict and not _project_intent_guard(query, payload):
            continue
        payload_scope = str(payload.get("doc_scope") or infer_scope(str(payload.get("path") or "")))
        result_rows.append(
            {
                "rank": rank,
                "score": effective_score,
                "doc_path": payload.get("path"),
                "doc_title": payload.get("title"),
                "snippet": build_snippet(payload.get("text", ""), payload.get("highlight")),
                "citation": {
                    "chunk_id": payload.get("chunk_id"),
                    "start_char": payload.get("start_char"),
                    "end_char": payload.get("end_char"),
                },
                "signals": {
                    "bm25_rank": row.bm25_rank,
                    "vector_rank": row.vector_rank,
                    "fusion_method": "rrf",
                    "scope": payload_scope,
                    "active": bool(payload.get("doc_active")),
                },
            }
        )
        if len(result_rows) >= limit:
            break

    sources = collect_sources(result_rows)
    summary = None
    summary_html = None
    if summarize:
        summary = (
            f"Aucun resultat pour la requete: {query}"
            if not result_rows
            else _summarize_with_openrouter(query, result_rows, cfg, summary_top_k)
        )
        summary_html = render_markdown_safe(summary)

    return {
        "query": query,
        "results": result_rows,
        "sources": sources,
        "summary": summary,
        "summary_html": summary_html,
    }


def _build_index_html() -> str:
    return _load_asset_text("index.html")


def create_app(config_path: str, use_hybrid_default: bool = False) -> Any:
    cfg = load_config(config_path)
    app = FastAPI(title="searchctl-web", docs_url=None, redoc_url=None)
    app.state.cfg = cfg
    app.state.use_hybrid_default = use_hybrid_default

    def _json_error(message: str, status_code: int) -> Any:
        return JSONResponse({"error": message}, status_code=status_code)

    @app.get("/", response_class=HTMLResponse)
    async def web_index() -> Any:
        return _build_index_html()

    @app.get("/static/app.css")
    async def web_css() -> Any:
        return Response(_load_asset_text("app.css"), media_type="text/css; charset=utf-8")

    @app.get("/static/app.js")
    async def web_js() -> Any:
        return Response(_load_asset_text("app.js"), media_type="application/javascript; charset=utf-8")

    @app.get("/api/documents")
    async def list_documents() -> Any:
        db = MetadataDB(cfg.metadata.sqlite_path)
        db.init_schema()
        docs = [
            {
                "doc_id": row["doc_id"],
                "path": row["path"],
                "title": row["title"],
                "source_type": row["source_type"],
                "status": row["status"],
                "updated_at": row["updated_at"],
            }
            for row in db.list_documents()
        ]
        docs.sort(key=lambda item: int(item["updated_at"] or 0), reverse=True)
        return {"documents": docs}

    @app.get("/api/documents/{doc_id}")
    async def get_document(doc_id: str) -> Any:
        db = MetadataDB(cfg.metadata.sqlite_path)
        db.init_schema()
        row = db.get_document(doc_id)
        if not row:
            return _json_error("document not found", 404)
        doc = dict(row)
        try:
            content = _read_doc_content(doc, cfg)
        except PermissionError as exc:
            return _json_error(str(exc), 403)
        except FileNotFoundError as exc:
            return _json_error(str(exc), 404)

        return {
            "doc_id": doc["doc_id"],
            "path": doc["path"],
            "title": doc["title"],
            "source_type": doc["source_type"],
            "content": content,
            "rendered_html": render_markdown_safe(content) if doc["source_type"] == "markdown" else None,
        }

    @app.post("/api/search")
    async def search_api(request: Request) -> Any:
        try:
            raw = await request.body()
            if len(raw) > MAX_BODY_BYTES:
                return _json_error("request body too large", 400)
            body = json.loads(raw.decode("utf-8")) if raw else {}
            query = str(body.get("query") or "").strip()
            if not query:
                return _json_error("query is required", 400)
            payload = _search_rows(
                cfg=cfg,
                query=query,
                top=int(body.get("top")) if body.get("top") is not None else None,
                summarize=bool(body.get("summarize", False)),
                summary_top_k=int(body.get("summary_top_k", 8)),
                use_hybrid=bool(body.get("use_hybrid", app.state.use_hybrid_default)),
                summary_use_hybrid=bool(body.get("summary_use_hybrid", False)),
                strict=bool(body.get("strict", False)),
            )
            return payload
        except ValueError as exc:
            return _json_error(str(exc), 400)
        except RuntimeError as exc:
            return _json_error(str(exc), 503)
        except Exception as exc:
            return _json_error(f"internal error: {exc}", 500)

    return app


def serve_web(
    config_path: str,
    host: str,
    port: int,
    allow_remote: bool,
    use_hybrid_default: bool = False,
) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Uvicorn is not installed. Run `pip install -e .` to install web dependencies.") from exc

    bind_host = resolve_bind_host(host, allow_remote)
    app = create_app(config_path, use_hybrid_default)
    print(f"Synexis web UI available at http://{bind_host}:{port}")
    uvicorn.run(app, host=bind_host, port=port, log_level="info")

from __future__ import annotations

import json
import re
import unicodedata
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from opensearchpy.exceptions import NotFoundError

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


def _search_rows(
    cfg: AppConfig,
    query: str,
    top: int | None,
    summarize: bool,
    summary_top_k: int,
    summary_use_hybrid: bool,
    strict: bool,
) -> dict[str, Any]:
    os_client = make_opensearch_client(cfg.opensearch.url)
    use_vector = (not summarize) or summary_use_hybrid
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
    if summarize:
        summary = (
            f"Aucun resultat pour la requete: {query}"
            if not result_rows
            else _summarize_with_openrouter(query, result_rows, cfg, summary_top_k)
        )

    return {"query": query, "results": result_rows, "sources": sources, "summary": summary}


class _WebState:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg


class SearchWebHandler(BaseHTTPRequestHandler):
    server_version = "searchctl-web/0.1"

    def _state(self) -> _WebState:
        return self.server.state  # type: ignore[attr-defined]

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html: str) -> None:
        raw = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict[str, Any]:
        length_header = self.headers.get("Content-Length") or "0"
        length = int(length_header)
        if length <= 0:
            return {}
        if length > MAX_BODY_BYTES:
            raise ValueError("request body too large")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        cfg = self._state().cfg
        if self.path == "/":
            self._send_html(_build_index_html())
            return

        if self.path == "/api/documents":
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
            self._send_json({"documents": docs})
            return

        if self.path.startswith("/api/documents/"):
            doc_id = self.path.rsplit("/", 1)[-1]
            db = MetadataDB(cfg.metadata.sqlite_path)
            db.init_schema()
            row = db.get_document(doc_id)
            if not row:
                self._send_json({"error": "document not found"}, status=404)
                return
            doc = dict(row)
            try:
                content = _read_doc_content(doc, cfg)
            except PermissionError as exc:
                self._send_json({"error": str(exc)}, status=403)
                return
            except FileNotFoundError as exc:
                self._send_json({"error": str(exc)}, status=404)
                return
            self._send_json(
                {
                    "doc_id": doc["doc_id"],
                    "path": doc["path"],
                    "title": doc["title"],
                    "source_type": doc["source_type"],
                    "content": content,
                }
            )
            return

        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        cfg = self._state().cfg
        if self.path != "/api/search":
            self._send_json({"error": "not found"}, status=404)
            return
        try:
            body = self._read_json_body()
            query = str(body.get("query") or "").strip()
            if not query:
                self._send_json({"error": "query is required"}, status=400)
                return
            payload = _search_rows(
                cfg=cfg,
                query=query,
                top=int(body.get("top")) if body.get("top") is not None else None,
                summarize=bool(body.get("summarize", False)),
                summary_top_k=int(body.get("summary_top_k", 8)),
                summary_use_hybrid=bool(body.get("summary_use_hybrid", False)),
                strict=bool(body.get("strict", False)),
            )
            self._send_json(payload)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=503)
        except Exception as exc:  # keep explicit envelope for frontend
            self._send_json({"error": f"internal error: {exc}"}, status=500)


def _build_index_html() -> str:
    return """<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Synexis Web</title>
  <style>
    :root {
      --bg: #f6f1e8;
      --panel: #fff9f0;
      --ink: #1f2328;
      --muted: #5b6470;
      --accent: #0f766e;
      --border: #e5dccf;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Georgia, "Times New Roman", serif; color: var(--ink); background: radial-gradient(circle at top right, #fff5e6, var(--bg)); }
    header { padding: 16px 20px; border-bottom: 1px solid var(--border); background: #fffdf9; }
    h1 { margin: 0; font-size: 1.3rem; }
    main { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 12px; }
    .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 12px; min-height: 300px; }
    .row { display: flex; gap: 8px; align-items: center; }
    input, button, select, textarea { font: inherit; border-radius: 8px; border: 1px solid var(--border); padding: 8px; }
    textarea { width: 100%; min-height: 120px; }
    button { background: var(--accent); color: white; border: 0; cursor: pointer; }
    ul { list-style: none; padding: 0; margin: 8px 0 0; }
    li { padding: 8px; border-bottom: 1px solid var(--border); }
    li:hover { background: #f8efe0; cursor: pointer; }
    pre { white-space: pre-wrap; background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 10px; max-height: 420px; overflow: auto; }
    .muted { color: var(--muted); font-size: 0.9rem; }
    @media (max-width: 980px) { main { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>Synexis Web</h1>
    <div class=\"muted\">Recherche hybride, synthèse et consultation des documents indexés.</div>
  </header>
  <main>
    <section class=\"panel\">
      <div class=\"row\">
        <input id=\"query\" placeholder=\"Requête\" style=\"flex:1\" />
        <label><input id=\"summarize\" type=\"checkbox\" /> synthèse</label>
        <button id=\"searchBtn\">Rechercher</button>
      </div>
      <div id=\"summary\" class=\"muted\" style=\"margin-top:8px\"></div>
      <ul id=\"results\"></ul>
    </section>
    <section class=\"panel\">
      <div class=\"row\" style=\"justify-content:space-between\">
        <strong>Documents indexés</strong>
        <button id=\"refreshBtn\">Rafraîchir</button>
      </div>
      <ul id=\"docs\"></ul>
      <h3>Contenu</h3>
      <pre id=\"docContent\">Sélectionnez un document.</pre>
    </section>
  </main>
  <script>
    async function api(path, payload) {
      const opts = payload ? { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) } : {};
      const res = await fetch(path, opts);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
      return data;
    }

    function setText(id, text) { document.getElementById(id).textContent = text || ''; }

    async function runSearch() {
      const query = document.getElementById('query').value.trim();
      if (!query) return;
      const summarize = document.getElementById('summarize').checked;
      try {
        const out = await api('/api/search', {query, summarize});
        setText('summary', summarize ? (out.summary || '') : '');
        const root = document.getElementById('results');
        root.innerHTML = '';
        for (const row of out.results || []) {
          const li = document.createElement('li');
          li.innerHTML = '<strong>#' + row.rank + ' ' + (row.doc_title || '(untitled)') + '</strong><br>' +
            '<span class="muted">' + (row.doc_path || '') + '</span><br>' +
            (row.snippet || '') + '<br>' +
            '<span class="muted">chunk=' + (row.citation?.chunk_id || '') + '</span>';
          root.appendChild(li);
        }
      } catch (err) {
        setText('summary', String(err));
      }
    }

    async function loadDocs() {
      try {
        const out = await api('/api/documents');
        const root = document.getElementById('docs');
        root.innerHTML = '';
        for (const doc of out.documents || []) {
          const li = document.createElement('li');
          li.textContent = (doc.title || '(untitled)') + ' [' + (doc.source_type || '?') + ']';
          li.title = doc.path || '';
          li.onclick = () => openDoc(doc.doc_id);
          root.appendChild(li);
        }
      } catch (err) {
        setText('docContent', String(err));
      }
    }

    async function openDoc(docId) {
      try {
        const out = await api('/api/documents/' + encodeURIComponent(docId));
        setText('docContent', out.content || '');
      } catch (err) {
        setText('docContent', String(err));
      }
    }

    document.getElementById('searchBtn').onclick = runSearch;
    document.getElementById('refreshBtn').onclick = loadDocs;
    document.getElementById('query').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') runSearch();
    });
    loadDocs();
  </script>
</body>
</html>
"""


def serve_web(config_path: str, host: str, port: int, allow_remote: bool) -> None:
    cfg = load_config(config_path)
    bind_host = resolve_bind_host(host, allow_remote)
    server = ThreadingHTTPServer((bind_host, port), SearchWebHandler)
    server.state = _WebState(cfg)  # type: ignore[attr-defined]
    print(f"Synexis web UI available at http://{bind_host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

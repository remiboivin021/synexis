from __future__ import annotations

import json
import logging
import time

import typer
import uvicorn

from rag.api.server import create_app
from rag.config import RagConfig
from rag.generation.chain import answer_question
from rag.ingestion.pipeline import ingest_path
from rag.logging import configure_logging
from rag.retrieval.retriever import retrieve_documents

app = typer.Typer(help="RAG LangChain CLI")
LOG = logging.getLogger("rag.cli")


@app.command()
def ingest(
    path: str = typer.Option(..., "--path"),
    glob: str = typer.Option("**/*", "--glob"),
    tenant_id: str | None = typer.Option(None, "--tenant-id"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    cfg = RagConfig.from_env()
    configure_logging(cfg.log_level)
    start = time.perf_counter()
    result = ingest_path(cfg, path=path, glob=glob, tenant_id=tenant_id, dry_run=dry_run)
    result["timing_ms"] = {"ingest": int((time.perf_counter() - start) * 1000)}
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command()
def query(
    question: str = typer.Option(..., "--question"),
    tenant_id: str | None = typer.Option(None, "--tenant-id"),
    doc_id: str | None = typer.Option(None, "--doc-id"),
    source: str | None = typer.Option(None, "--source"),
    debug: int = typer.Option(1, "--debug"),
) -> None:
    cfg = RagConfig.from_env()
    configure_logging(cfg.log_level)

    timings: dict[str, int] = {}
    start_retrieve = time.perf_counter()
    docs, retrieval_debug = retrieve_documents(
        cfg,
        question,
        filters={"tenant_id": tenant_id, "doc_id": doc_id, "source": source},
    )
    timings["retrieve"] = int((time.perf_counter() - start_retrieve) * 1000)

    start_generate = time.perf_counter()
    result = answer_question(cfg, question, docs, retrieval_debug=retrieval_debug)
    timings["generate"] = int((time.perf_counter() - start_generate) * 1000)

    if debug:
        result.setdefault("debug", {})
        result["debug"].setdefault("timing_ms", {})
        result["debug"]["timing_ms"].update(timings)

    LOG.info(
        "query.complete question=%s citations=%s timing_ms=%s",
        question,
        len(result.get("citations", [])),
        result.get("debug", {}).get("timing_ms", {}),
    )
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8090, "--port"),
) -> None:
    cfg = RagConfig.from_env()
    configure_logging(cfg.log_level)
    uvicorn.run(create_app(cfg), host=host, port=port)


if __name__ == "__main__":
    app()

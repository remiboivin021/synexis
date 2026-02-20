import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="set RUN_E2E=1 to run backend integration")
def test_e2e_ingest_search(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note1.md").write_text("# Note One\nSynexis is a local first search engine.", encoding="utf-8")
    (vault / "note2.md").write_text("# Note Two\nHybrid retrieval combines bm25 and vectors.", encoding="utf-8")
    (vault / "a.txt").write_text("Deterministic pipeline execution.", encoding="utf-8")

    # Minimal pseudo-pdf fixture placeholder for corpus shape in v1 tests.
    (vault / "small.pdf").write_bytes(b"%PDF-1.4\n%%EOF")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                f'roots: ["{vault.as_posix()}"]',
                'include_extensions: [".md", ".pdf", ".txt"]',
                "exclude_globs: []",
                "chunking:",
                "  target_chars: 2200",
                "  overlap_chars: 250",
                "  min_chunk_chars: 1",
                "embeddings:",
                '  model_name: "intfloat/e5-small-v2"',
                "  batch_size: 4",
                '  device: "cpu"',
                "opensearch:",
                '  url: "http://localhost:9200"',
                '  index_name: "personal_chunks_v1"',
                "qdrant:",
                '  url: "http://localhost:6333"',
                '  collection_name: "personal_chunks_v1"',
                "  vector_size: 384",
                '  distance: "Cosine"',
                "indexing:",
                '  reindex_policy: "incremental"',
                "  max_workers: 1",
                "search:",
                "  bm25_top_k: 10",
                "  vector_top_k: 10",
                '  fusion: "rrf"',
                "  rrf_k: 60",
                '  rerank: "off"',
                "  rerank_top_k: 10",
                "  return_top_n: 5",
                "  collapse_by_doc_default: false",
                "metadata:",
                f'  sqlite_path: "{(tmp_path / "metadata.db").as_posix()}"',
                f'  extracted_text_cache_dir: "{(tmp_path / "cache").as_posix()}"',
            ]
        ),
        encoding="utf-8",
    )

    subprocess.run(["searchctl", "ingest", "--config", str(cfg)], check=True)
    proc = subprocess.run(
        ["searchctl", "search", "synexis local", "--config", str(cfg), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = json.loads(proc.stdout)
    assert rows
    for key in ["rank", "score", "doc_path", "doc_title", "snippet", "citation", "signals"]:
        assert key in rows[0]

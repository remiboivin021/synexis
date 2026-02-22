#!/usr/bin/env bash
set -euo pipefail

python -m rag.cli ingest --path "${1:-./data/raw}" "${@:2}"

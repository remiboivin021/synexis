#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 \"question\" [extra args]" >&2
  exit 1
fi

question="$1"
shift
python -m rag.cli query --question "$question" "$@"

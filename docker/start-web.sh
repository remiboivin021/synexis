#!/bin/sh
set -eu

VENV_PATH="${VIRTUAL_ENV:-/home/synexis/.venv}"
NEEDS_REBUILD=0

# Rebuild invalid or empty venv mounted from volume.
if [ ! -x "$VENV_PATH/bin/python" ]; then
    NEEDS_REBUILD=1
elif ! "$VENV_PATH/bin/python" -c "import sys" >/dev/null 2>&1; then
    NEEDS_REBUILD=1
fi

if [ "$NEEDS_REBUILD" -eq 0 ] && [ -f "$VENV_PATH/bin/searchctl" ]; then
    SEARCHCTL_PY="$(sed -n '1s/^#!//p' "$VENV_PATH/bin/searchctl" || true)"
    if [ -n "$SEARCHCTL_PY" ] && [ ! -x "$SEARCHCTL_PY" ]; then
        NEEDS_REBUILD=1
    fi
fi

if [ "$NEEDS_REBUILD" -eq 1 ] || [ ! -x "$VENV_PATH/bin/searchctl" ]; then
    mkdir -p "$VENV_PATH"
    find "$VENV_PATH" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    uv venv --python 3.14 --seed "$VENV_PATH"
    "$VENV_PATH/bin/pip" install --upgrade pip
    "$VENV_PATH/bin/pip" install .
fi

exec "$VENV_PATH/bin/python" -m searchctl.cli web --config config.yaml --host 0.0.0.0 --port 10000 --allow-remote

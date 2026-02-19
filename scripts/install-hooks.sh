#!/usr/bin/env sh
set -eu

ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$ROOT/synexis_brain/git_hooks"
HOOKS_DST="$(git rev-parse --git-path hooks)"

mkdir -p "$HOOKS_DST"
cp "$HOOKS_SRC/pre-commit" "$HOOKS_DST/pre-commit"
cp "$HOOKS_SRC/prepare-commit-msg" "$HOOKS_DST/prepare-commit-msg"
cp "$HOOKS_SRC/commit-msg" "$HOOKS_DST/commit-msg"
chmod +x "$HOOKS_DST/pre-commit" "$HOOKS_DST/prepare-commit-msg" "$HOOKS_DST/commit-msg"

echo "Installed hooks into $HOOKS_DST"

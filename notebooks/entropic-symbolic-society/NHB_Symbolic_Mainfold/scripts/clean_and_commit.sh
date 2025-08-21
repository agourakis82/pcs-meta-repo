#!/usr/bin/env bash
# clean_and_commit.sh — Strip notebook outputs and prepare a clean commit.
# Usage:
#   bash scripts/clean_and_commit.sh "Your concise commit message"
#
# What it does:
#   1) Clears outputs from all .ipynb files in notebooks/
#   2) Removes typical temp/cache artifacts
#   3) Shows a short git status + diffstat
#   4) Stages changes and creates a commit with the provided message

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMMIT_MSG="${1:-chore: clean notebooks and update assets}"

echo "[INFO] Project root: $ROOT_DIR"
echo "[INFO] Commit message: $COMMIT_MSG"

# 1) Clear notebook outputs (requires jupyter installed in the env)
if ! command -v jupyter >/dev/null 2>&1; then
  echo "[ERROR] 'jupyter' not found in PATH. Activate your env or run reset_env.sh first."
  exit 1
fi

echo "[INFO] Clearing outputs from notebooks/*.ipynb ..."
shopt -s nullglob
for nb in notebooks/*.ipynb; do
  echo "  - $nb"
  jupyter nbconvert --clear-output --inplace "$nb"
done
shopt -u nullglob

# 2) Remove temp/cache artifacts safely
echo "[INFO] Removing temporary files ..."
find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
find . -type f -name "*.pyc" -delete || true
find . -type f -name "*.pyo" -delete || true
find . -type f -name "*.tmp" -delete || true
find results -type f -name "*.png" -size +50M -print -delete 2>/dev/null || true

# 3) Show git status + diffstat
if command -v git >/dev/null 2>&1; then
  echo "[INFO] Git status before staging:"
  git status --short
  echo "[INFO] Diffstat:"
  git diff --stat || true

  # 4) Stage and commit
  echo "[INFO] Staging changes ..."
  git add -A
  echo "[INFO] Creating commit ..."
  git commit -m "$COMMIT_MSG" || {
    echo "[WARN] Nothing to commit or commit failed."
    exit 0
  }
  echo "[DONE] Commit created."
else
  echo "[WARN] Git not found. Skipping commit step."
fi

echo "[SUCCESS] Cleanup finished."

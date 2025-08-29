#!/usr/bin/env bash
set -euo pipefail

# Usage: ./apply_agent_pack.sh <repo_url_or_path> [branch_name]
# Example: ./apply_agent_pack.sh https://github.com/agourakis82/phd-bridge-biomaterials-neuro-symbolic.git chore/agent-pack

REPO="${1:-}"
BRANCH="${2:-chore/agent-pack}"

if [[ -z "$REPO" ]]; then
  echo "Usage: $0 <repo_url_or_path> [branch_name]" >&2
  exit 1
fi

# If REPO is a URL, clone; else assume it's an existing path
if [[ "$REPO" =~ ^https?:// ]]; then
  tmpdir="$(mktemp -d)"
  git clone "$REPO" "$tmpdir/repo"
  cd "$tmpdir/repo"
else
  cd "$REPO"
fi

# Ensure gh is authenticated
if ! gh auth status >/dev/null 2>&1; then
  echo "[!] gh CLI not authenticated. Run: gh auth login" >&2
  exit 1
fi

# Create branch
git checkout -b "$BRANCH" || git checkout "$BRANCH"

# Unzip starter pack to repo root
unzip -o ../github-agent-starter-pack.zip -d ./ || unzip -o ./github-agent-starter-pack.zip -d ./ || {
  echo "[!] Place github-agent-starter-pack.zip alongside this script or in repo root."; exit 1;
}

# Optional: install pre-commit if Python present
if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --upgrade pip pre-commit >/dev/null 2>&1 || true
  pre-commit install || true
fi

git add -A
git commit -m "chore(ops): add agent starter pack (CI, templates, pre-commit)" || true
git push -u origin "$BRANCH"

# Open PR
gh pr create --title "chore(ops): agent starter pack" --body "Adds CI, templates, link checks and pre-commit to reduce chores." --fill || true

echo "[OK] Agent pack applied and PR created (if permissions allow)."

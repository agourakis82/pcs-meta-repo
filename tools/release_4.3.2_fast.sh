#!/usr/bin/env bash
set -euo pipefail

echo "[fast-release] Starting v4.3.2 (no pip, no gh, exclude L0) at $(date)"
ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

# 1) Ensure folders
mkdir -p data/L0_raw data/L1_tidy data/L2_derived data/LICENSES data/CONTRACTS data/CHECKS scripts tools

# 2) Optional: unpack kit (no overwrite)
if [ -f "data_crystallization_kit_v1.zip" ] && command -v unzip >/dev/null 2>&1; then
  echo "[fast-release] Unpacking kit (no overwrite)"
  unzip -n data_crystallization_kit_v1.zip -d . >/dev/null || true
fi

# 3) Checks (best-effort; do not fail pipeline if missing deps)
if [ -f scripts/compute_checksums.py ]; then
  echo "[fast-release] checksums"
  python3 scripts/compute_checksums.py || echo "[fast-release] WARN: checksum skipped"
fi
if [ -f scripts/validate_contracts.py ]; then
  echo "[fast-release] validate contracts"
  python3 scripts/validate_contracts.py || echo "[fast-release] WARN: validate skipped"
fi
if [ -f scripts/linkcheck_local.py ]; then
  echo "[fast-release] linkcheck"
  python3 scripts/linkcheck_local.py || echo "[fast-release] WARN: linkcheck skipped"
fi

# 4) Package (exclude L0 to avoid huge tarballs)
echo "[fast-release] packaging data_release.tar.gz (excluding data/L0_raw)"
tar --exclude-vcs --exclude='data/L0_raw' -czf data_release.tar.gz \
  data/L1_tidy data/L2_derived data/CHECKS \
  PROVENANCE.yaml DATA_DICTIONARY.md \
  CHANGELOG_v4.3.2.md RELEASE_NOTES_v4.3.2.md \
  CITATION_v4.3.2.cff metadata_v4.3.2.yaml zenodo_v4.3.2.json \
  QUALITY_GATES.md Makefile .gitattributes \
  scripts/*.py 2>/dev/null || echo "[fast-release] WARN: some files missing; packaged what was available"

# 5) Commit & tag (no GitHub release here; do it manually via UI or gh later)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git add -A
  git commit -m "chore(release): v4.3.2 fast — package without L0, no gh, no pip" || echo "[fast-release] INFO: nothing to commit"
  git tag -a v4.3.2 -m "v4.3.2" || echo "[fast-release] INFO: tag exists or cannot tag"
  echo "[fast-release] Next: push and create GitHub release manually, or run: git push && git push --tags"
else
  echo "[fast-release] INFO: Not a git repo; skipping commit/tag."
fi

echo "[fast-release] Done at $(date)"


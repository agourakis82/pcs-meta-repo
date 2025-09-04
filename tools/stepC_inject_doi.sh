#!/usr/bin/env bash
set -euo pipefail

DOI="${1:-}"
if [ -z "$DOI" ]; then
  echo "Usage: tools/stepC_inject_doi.sh <DOI>" >&2
  exit 1
fi

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

python3 - "$DOI" <<'PY'
import sys, re, pathlib
doi=sys.argv[1]
p_cff=pathlib.Path('CITATION_v4.3.2.cff')
if p_cff.exists():
    t=p_cff.read_text(encoding='utf-8')
    t2, _ = re.subn(r'(?m)^doi:\s*""\s*$', f'doi: "{doi}"', t)
    p_cff.write_text(t2, encoding='utf-8')
p_meta=pathlib.Path('metadata_v4.3.2.yaml')
if p_meta.exists():
    m=p_meta.read_text(encoding='utf-8')
    m2, _ = re.subn(r'(?m)^version_doi:\s*""\s*$', f'version_doi: "{doi}"', m)
    p_meta.write_text(m2, encoding='utf-8')
print('[inject-doi] Updated local files.')
PY

git add CITATION_v4.3.2.cff metadata_v4.3.2.yaml || true
git commit -m "docs: add Version DOI to v4.3.2" || echo "[inject-doi] INFO: nothing to commit"
echo "[inject-doi] Done. Push with: git push"


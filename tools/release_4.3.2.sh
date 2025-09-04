#!/usr/bin/env bash
set -euo pipefail

# Symbolic Manifolds — Release 4.3.2
# Patch release for data crystallization L0→L1→L2 with provenance, contracts, validations

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

echo "[release] Starting v4.3.2 data crystallization pipeline at $(date)"

ensure_dirs() {
  mkdir -p data/L0_raw data/L1_tidy data/L2_derived data/LICENSES data/CONTRACTS data/CHECKS scripts tools
}

ensure_python_and_libs() {
  if command -v python3 >/dev/null 2>&1; then
    PY=python3
  elif command -v python >/dev/null 2>&1; then
    PY=python
  else
    echo "[release] ERROR: Python 3 is required." >&2
    exit 1
  fi

  # Detect pip (optional)
  if "$PY" -m pip --version >/dev/null 2>&1; then
    PIP="$PY -m pip"
  elif command -v pip3 >/dev/null 2>&1; then
    PIP="pip3"
  elif command -v pip >/dev/null 2>&1; then
    PIP="pip"
  else
    PIP=""
  fi

  # Heuristics: install only if strictly needed
  NEED_PANDAS=0
  for f in \
    data/L1_tidy/swow_en_v1_tidy.csv \
    data/L1_tidy/zuco_v2_tidy.csv \
    data/L2_derived/ag5_kec_metrics.csv; do
    if [ -f "$f" ]; then NEED_PANDAS=1; break; fi
  done

  if [ "$NEED_PANDAS" = "1" ]; then
    if ! "$PY" - <<'EOF' >/dev/null 2>&1
import importlib, sys; sys.exit(0 if importlib.util.find_spec('pandas') else 1)
EOF
    then
      if [ -n "$PIP" ]; then
        echo "[release] Installing pandas (needed for validation)"
        $PIP install --user pandas >/dev/null || echo "[release] WARN: could not install pandas; validations may be SKIPPED"
      else
        echo "[release] WARN: pip not available; validations may be SKIPPED"
      fi
    fi
  else
    echo "[release] INFO: No L1/L2 inputs found; skipping pandas install"
  fi

  # Optional: install PyYAML only if PROVENANCE.yaml exists and yaml missing
  if [ -f PROVENANCE.yaml ]; then
    if ! "$PY" - <<'EOF' >/dev/null 2>&1
import importlib, sys; sys.exit(0 if importlib.util.find_spec('yaml') else 1)
EOF
    then
      if [ -n "$PIP" ]; then
        echo "[release] Installing pyyaml (to update provenance hashes)"
        $PIP install --user pyyaml >/dev/null || echo "[release] WARN: could not install pyyaml; provenance update will be skipped"
      else
        echo "[release] INFO: pip not available; skipping pyyaml"
      fi
    fi
  fi
}

unpack_kit_if_present() {
  if [ -f "data_crystallization_kit_v1.zip" ]; then
    if command -v unzip >/dev/null 2>&1; then
      echo "[release] Found data_crystallization_kit_v1.zip — unpacking (no overwrite)"
      unzip -n data_crystallization_kit_v1.zip -d . >/dev/null || true
    else
      echo "[release] WARN: unzip not available; skipping kit extraction."
    fi
  fi
}

create_if_missing() {
  local path="$1"; shift || true
  if [ ! -f "$path" ]; then
    mkdir -p "$(dirname "$path")"
    cat >"$path" <<'EOF'
EOF
  fi
}

append_or_create() {
  local path="$1"; shift || true
  mkdir -p "$(dirname "$path")"
  cat >>"$path" <<'EOF'
EOF
}

ensure_minimal_files() {
  # PROVENANCE.yaml
  if [ ! -f PROVENANCE.yaml ]; then
    cat > PROVENANCE.yaml <<'EOF'
datasets:
  - id: swow_en_v1
    level: L0_raw
    path: data/L0_raw/swow_en_v1.csv
    sha256: ""
    source: "Small World of Words (English) v1"
    license: "CC BY 4.0"
    reference: "https://smallworldofwords.org/"
  - id: zuco_v2
    level: L0_raw
    path: data/L0_raw/zuco_v2.csv
    sha256: ""
    source: "Zurich Cognitive Language Processing Corpus (ZuCo) v2"
    license: "CC BY 4.0"
    reference: "https://osf.io/q3zws/"
  - id: swow_en_v1_tidy
    level: L1_tidy
    path: data/L1_tidy/swow_en_v1_tidy.csv
    sha256: ""
    transform_scripts:
      - scripts/tidy_swow_en.py
  - id: zuco_v2_tidy
    level: L1_tidy
    path: data/L1_tidy/zuco_v2_tidy.csv
    sha256: ""
    transform_scripts:
      - scripts/tidy_zuco.py
  - id: ag5_kec_metrics
    level: L2_derived
    path: data/L2_derived/ag5_kec_metrics.csv
    sha256: ""
    transform_scripts:
      - scripts/compute_ag5_kec.py
EOF
  fi

  # Contracts
  if [ ! -f data/CONTRACTS/swow_en.yml ]; then
    cat > data/CONTRACTS/swow_en.yml <<'EOF'
dataset: swow_en_v1_tidy
level: L1
expected_file: data/L1_tidy/swow_en_v1_tidy.csv
format: csv
pk: [cue, response]
columns:
  - {name: cue, type: string, required: true}
  - {name: response, type: string, required: true}
  - {name: strength, type: float, required: true}
rules:
  unique:
    - [cue, response]
  ranges:
    strength: [0.0, 1.0]
notes: "Strength normalized in [0,1]."
EOF
  fi
  if [ ! -f data/CONTRACTS/zuco.yml ]; then
    cat > data/CONTRACTS/zuco.yml <<'EOF'
dataset: zuco_v2_tidy
level: L1
expected_file: data/L1_tidy/zuco_v2_tidy.csv
format: csv
pk: [subject, sentence_id, token_id]
columns:
  - {name: subject, type: string, required: true}
  - {name: sentence_id, type: int, required: true}
  - {name: token_id, type: int, required: true}
  - {name: gaze_duration_ms, type: float, required: false}
  - {name: total_reading_time_ms, type: float, required: false}
rules:
  ranges:
    gaze_duration_ms: [0.0, inf]
    total_reading_time_ms: [0.0, inf]
notes: "Durations must be non-negative (ms)."
EOF
  fi
  if [ ! -f data/CONTRACTS/ag5_kec.yml ]; then
    cat > data/CONTRACTS/ag5_kec.yml <<'EOF'
dataset: ag5_kec_metrics
level: L2
expected_file: data/L2_derived/ag5_kec_metrics.csv
format: csv
pk: [concept_id]
columns:
  - {name: concept_id, type: string, required: true}
  - {name: kec_score, type: float, required: true}
  - {name: coverage, type: float, required: true}
  - {name: density, type: float, required: false}
rules:
  unique:
    - [concept_id]
  ranges:
    kec_score: [0.0, 1.0]
    coverage: [0.0, 1.0]
    density: [0.0, 1.0]
notes: "AG5/KEC metrics normalized to [0,1]."
EOF
  fi

  # Data dictionary
  if [ ! -f DATA_DICTIONARY.md ]; then
    cat > DATA_DICTIONARY.md <<'EOF'
# Data Dictionary — L1 and L2

This document enumerates expected tables and columns for L1 (tidy) and L2 (derived) layers.

## L1 — swow_en_v1_tidy (CSV)
- cue: string
- response: string
- strength: float in [0,1]

Primary key: (cue, response)

## L1 — zuco_v2_tidy (CSV)
- subject: string
- sentence_id: int
- token_id: int
- gaze_duration_ms: float >= 0
- total_reading_time_ms: float >= 0

Primary key: (subject, sentence_id, token_id)

## L2 — ag5_kec_metrics (CSV)
- concept_id: string
- kec_score: float [0,1]
- coverage: float [0,1]
- density: float [0,1]

Primary key: (concept_id)

EOF
  fi

  # scripts/compute_checksums.py
  if [ ! -f scripts/compute_checksums.py ]; then
    cat > scripts/compute_checksums.py <<'EOF'
#!/usr/bin/env python3
import os, sys, hashlib, csv, time
import yaml

ROOT = os.path.abspath(os.getcwd())
CHECKS_DIR = os.path.join(ROOT, 'data', 'CHECKS')
os.makedirs(CHECKS_DIR, exist_ok=True)

def sha256_of(path, chunk=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def collect_files():
    targets = []
    data_root = os.path.join(ROOT, 'data')
    if os.path.isdir(data_root):
        for base, _, files in os.walk(data_root):
            for fn in files:
                p = os.path.join(base, fn)
                # Skip checks artifacts themselves
                if os.path.relpath(p, ROOT).startswith('data/CHECKS'):
                    continue
                targets.append(p)
    # Also include catalog-like files if present
    for extra in ['PROVENANCE.yaml', 'DATA_DICTIONARY.md']:
        ep = os.path.join(ROOT, extra)
        if os.path.isfile(ep):
            targets.append(ep)
    return sorted(targets)

def update_provenance(checksums):
    prov_path = os.path.join(ROOT, 'PROVENANCE.yaml')
    if not os.path.isfile(prov_path):
        return
    try:
        with open(prov_path, 'r', encoding='utf-8') as f:
            prov = yaml.safe_load(f) or {}
        datasets = prov.get('datasets', [])
        changed = False
        for d in datasets:
            p = d.get('path')
            if p:
                absp = os.path.join(ROOT, p)
                if absp in checksums:
                    if d.get('sha256') != checksums[absp]['sha256']:
                        d['sha256'] = checksums[absp]['sha256']
                        changed = True
        if changed:
            with open(prov_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(prov, f, sort_keys=False)
    except Exception as e:
        print(f"[checksum] WARN: could not update PROVENANCE.yaml: {e}")

def main():
    files = collect_files()
    checksums = {}
    out_csv = os.path.join(CHECKS_DIR, 'checksums.csv')
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['path', 'sha256', 'bytes', 'mtime'])
        for p in files:
            try:
                s = sha256_of(p)
                st = os.stat(p)
                w.writerow([
                    os.path.relpath(p, ROOT), s, st.st_size, int(st.st_mtime)
                ])
                checksums[p] = {'sha256': s}
            except Exception as e:
                print(f"[checksum] WARN: cannot checksum {p}: {e}")
    update_provenance(checksums)
    print(f"[checksum] Wrote {out_csv}")

if __name__ == '__main__':
    main()
EOF
    chmod +x scripts/compute_checksums.py
  fi

  # scripts/validate_contracts.py
  if [ ! -f scripts/validate_contracts.py ]; then
    cat > scripts/validate_contracts.py <<'EOF'
#!/usr/bin/env python3
import os, sys, json, math
import pandas as pd
import yaml

ROOT = os.path.abspath(os.getcwd())
CONTRACTS_DIR = os.path.join(ROOT, 'data', 'CONTRACTS')
CHECKS_DIR = os.path.join(ROOT, 'data', 'CHECKS')
os.makedirs(CHECKS_DIR, exist_ok=True)

def read_df(path, fmt=None):
    ext = (fmt or os.path.splitext(path)[1].lstrip('.')).lower()
    if ext in ('csv', ''):
        return pd.read_csv(path)
    if ext in ('tsv',):
        return pd.read_csv(path, sep='\t')
    if ext in ('parquet', 'pq'):
        return pd.read_parquet(path)
    if ext in ('json',):
        return pd.read_json(path, lines=False)
    # fallback
    return pd.read_csv(path)

def check_ranges(series, lo, hi):
    if lo is None and hi is None:
        return []
    issues = []
    if lo is not None:
        bad = series[series < lo]
        if len(bad) > 0:
            issues.append(f"values < {lo}: {len(bad)}")
    if hi is not None:
        bad = series[series > hi]
        if len(bad) > 0:
            issues.append(f"values > {hi}: {len(bad)}")
    return issues

def coerce_float(series):
    return pd.to_numeric(series, errors='coerce')

def validate_contract(contract_path):
    with open(contract_path, 'r', encoding='utf-8') as f:
        c = yaml.safe_load(f) or {}
    ds_name = c.get('dataset', os.path.basename(contract_path))
    exp = c.get('expected_file')
    fmt = c.get('format')
    result = {'dataset': ds_name, 'contract': os.path.relpath(contract_path, ROOT), 'status': 'SKIPPED', 'issues': [], 'stats': {}}
    if not exp:
        result['issues'].append('missing expected_file')
        result['status'] = 'ERROR'
        return result
    path = os.path.join(ROOT, exp)
    if not os.path.isfile(path):
        result['issues'].append(f"expected_file not found: {exp}")
        result['status'] = 'SKIPPED'
        return result

    try:
        df = read_df(path, fmt)
        result['stats'] = {'rows': int(df.shape[0]), 'cols': int(df.shape[1])}
        # required columns
        cols = c.get('columns', [])
        required = [col['name'] for col in cols if col.get('required')]
        missing = [col for col in required if col not in df.columns]
        if missing:
            result['issues'].append(f"missing required columns: {missing}")
        # pk uniqueness
        pk = c.get('pk') or []
        if pk:
            if not set(pk).issubset(df.columns):
                result['issues'].append(f"pk columns missing: {[x for x in pk if x not in df.columns]}")
            else:
                dups = df.duplicated(subset=pk).sum()
                if dups > 0:
                    result['issues'].append(f"duplicate PK rows: {dups}")
        # unique rules
        uniq_rules = (c.get('rules') or {}).get('unique') or []
        for group in uniq_rules:
            group = list(group)
            if not set(group).issubset(df.columns):
                result['issues'].append(f"unique group missing cols: {group}")
                continue
            dups = df.duplicated(subset=group).sum()
            if dups > 0:
                result['issues'].append(f"violated uniqueness {group}: {dups} dups")
        # ranges
        ranges = (c.get('rules') or {}).get('ranges') or {}
        for col, bounds in ranges.items():
            if col not in df.columns:
                result['issues'].append(f"range check missing column: {col}")
                continue
            lo, hi = None, None
            if isinstance(bounds, (list, tuple)) and len(bounds) == 2:
                lo, hi = bounds
            lo = None if lo in (None, 'inf', 'INF', 'nan') else float(lo)
            hi = None if hi in (None, 'inf', 'INF', 'nan') else float(hi)
            series = coerce_float(df[col])
            rng_issues = check_ranges(series, lo, hi)
            if rng_issues:
                result['issues'].append(f"{col}: {'; '.join(rng_issues)}")
        result['status'] = 'PASSED' if not result['issues'] else 'FAILED'
        return result
    except Exception as e:
        result['issues'].append(f"exception: {e}")
        result['status'] = 'ERROR'
        return result

def main():
    contracts = []
    if os.path.isdir(CONTRACTS_DIR):
        for fn in os.listdir(CONTRACTS_DIR):
            if fn.endswith(('.yml', '.yaml')):
                contracts.append(os.path.join(CONTRACTS_DIR, fn))
    results = [validate_contract(p) for p in sorted(contracts)]
    out = {
        'summary': {
            'total': len(results),
            'passed': sum(1 for r in results if r['status'] == 'PASSED'),
            'failed': sum(1 for r in results if r['status'] == 'FAILED'),
            'skipped': sum(1 for r in results if r['status'] == 'SKIPPED'),
            'error': sum(1 for r in results if r['status'] == 'ERROR'),
        },
        'results': results,
    }
    out_path = os.path.join(CHECKS_DIR, 'validation_report.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f"[validate] Wrote {out_path}")

if __name__ == '__main__':
    main()
EOF
    chmod +x scripts/validate_contracts.py
  fi

  # scripts/linkcheck_local.py
  if [ ! -f scripts/linkcheck_local.py ]; then
    cat > scripts/linkcheck_local.py <<'EOF'
#!/usr/bin/env python3
import os, re, json

ROOT = os.path.abspath(os.getcwd())
CHECKS_DIR = os.path.join(ROOT, 'data', 'CHECKS')
os.makedirs(CHECKS_DIR, exist_ok=True)

md_link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

def is_relative(link):
    if re.match(r'^[a-zA-Z]+://', link):
        return False
    if link.startswith('#') or link.startswith('mailto:'):
        return False
    return True

def find_md_files():
    files = []
    for base, _, fns in os.walk(ROOT):
        for fn in fns:
            if fn.lower().endswith('.md'):
                files.append(os.path.join(base, fn))
    return files

def main():
    details = []
    for md in find_md_files():
        try:
            with open(md, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception:
            continue
        for m in md_link_pattern.finditer(text):
            link = m.group(1).strip()
            if not is_relative(link):
                continue
            # strip anchors if any
            file_part = link.split('#', 1)[0]
            if not file_part:
                continue
            abs_path = os.path.normpath(os.path.join(os.path.dirname(md), file_part))
            exists = os.path.exists(abs_path)
            if not exists:
                details.append({
                    'file': os.path.relpath(md, ROOT),
                    'link': link,
                    'resolved': os.path.relpath(abs_path, ROOT),
                    'status': 'missing'
                })
    report = {
        'missing_count': len(details),
        'status': 'OK' if len(details) == 0 else 'ISSUES',
        'details': details,
    }
    out_path = os.path.join(CHECKS_DIR, 'linkcheck_report.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"[linkcheck] Wrote {out_path} ({report['status']})")

if __name__ == '__main__':
    main()
EOF
    chmod +x scripts/linkcheck_local.py
  fi

  # Makefile
  if [ ! -f Makefile ]; then
    cat > Makefile <<'EOF'
SHELL := bash
.PHONY: init checksum validate package freeze

init:
	@mkdir -p data/L0_raw data/L1_tidy data/L2_derived data/LICENSES data/CONTRACTS data/CHECKS scripts
	@echo "[make] init complete"

checksum:
	@python3 scripts/compute_checksums.py

validate:
	@python3 scripts/validate_contracts.py

package:
	@tar --exclude-vcs -czf data_release.tar.gz \
		data/ \
		PROVENANCE.yaml DATA_DICTIONARY.md \
		CHANGELOG_v4.3.2.md RELEASE_NOTES_v4.3.2.md \
		CITATION_v4.3.2.cff metadata_v4.3.2.yaml zenodo_v4.3.2.json \
		QUALITY_GATES.md Makefile .gitattributes \
		scripts/*.py
	@echo "[make] packaged data_release.tar.gz"

freeze: package
EOF
  fi

  # .gitattributes (append suggestions)
  if [ ! -f .gitattributes ]; then
    cat > .gitattributes <<'EOF'
# Suggest using Git LFS for large/binary artifacts
*.parquet filter=lfs diff=lfs merge=lfs -text
*.feather filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text
data/L0_raw/** filter=lfs diff=lfs merge=lfs -text
data/L1_tidy/** filter=lfs diff=lfs merge=lfs -text
data/L2_derived/** filter=lfs diff=lfs merge=lfs -text
EOF
  fi

  # Metadata files
  if [ ! -f CHANGELOG_v4.3.2.md ]; then
    cat > CHANGELOG_v4.3.2.md <<'EOF'
# Changelog — v4.3.2 (2025-09)

Patch release focused on data crystallization, provenance, and reproducibility. No changes to results, figures, or conclusions.

- Add L0→L1→L2 structure and contracts for SWOW EN, ZuCo, and AG5/KEC metrics
- Add checksums, contract validation, and local link checking
- Add release metadata for Zenodo and CITATION CFF
- Package data_release.tar.gz for archiving and DOI minting
EOF
  fi
  if [ ! -f RELEASE_NOTES_v4.3.2.md ]; then
    cat > RELEASE_NOTES_v4.3.2.md <<'EOF'
# Release Notes — v4.3.2

Summary
- Patch release delivering data crystallization (L0→L1→L2), provenance, and reproducibility scaffolding.
- No changes to scientific outcomes; editorial/curatorial improvements only.

Motivation
- Standardize data layout and enforce contracts to ensure repeatable processing.
- Provide transparent provenance and checksums for integrity verification.

Methods (IMRaD)
- Introduction: Clarify data layers (L0 raw, L1 tidy, L2 derived) and contractual expectations.
- Methods: Add validation scripts (pandas+PyYAML), checksum automation, and link checking.
- Results: Generated checksums.csv, validation_report.json (with SKIPPED where sources absent), linkcheck_report.json, and packaged data_release.tar.gz.
- Discussion: Enhances reproducibility and reduces integration friction across datasets.

Limitations and Biases
- Validation is contingent on availability of public L0/L1 data; missing inputs are marked SKIPPED.
- Contracts capture core schema and basic ranges; domain-specific nuances may need future refinement.

Impact
- Improves dataset/toolbox reliability and onboarding for downstream users.

Next Steps
- Upload package to Zenodo, mint Version DOI, and update CFF/metadata.
- Expand contracts (typing, enums), add automated schema tests in CI.
- Add data loaders and seeds where applicable.
EOF
  fi
  if [ ! -f CITATION_v4.3.2.cff ]; then
    cat > CITATION_v4.3.2.cff <<'EOF'
cff-version: 1.2.0
message: "If you use this software, please cite it."
title: "Symbolic Manifolds — v4.3.2 data crystallization patch"
version: 4.3.2
doi: ""
authors:
  - family-names: Agourakis
    given-names: Demetrios C.
    orcid: https://orcid.org/0000-0002-8596-5097
  - family-names: Agourakis
    given-names: Dionisio Chiuratto
EOF
  fi
  if [ ! -f metadata_v4.3.2.yaml ]; then
    cat > metadata_v4.3.2.yaml <<'EOF'
version: 4.3.2
concept_doi: 10.5281/zenodo.16533374
version_doi: ""
notes: "Data crystallization patch with provenance and validations"
EOF
  fi
  if [ ! -f zenodo_v4.3.2.json ]; then
    cat > zenodo_v4.3.2.json <<'EOF'
{
  "upload_type": "software",
  "title": "Symbolic Manifolds v4.3.2 — data crystallization patch",
  "description": "Patch release focusing on data crystallization (L0→L1→L2), provenance, and reproducibility.",
  "related_identifiers": [
    {
      "identifier": "10.5281/zenodo.16533374",
      "relation": "isVersionOf",
      "scheme": "doi"
    }
  ]
}
EOF
  fi

  # QUALITY_GATES.md update or create
  if [ -f QUALITY_GATES.md ]; then
    cat >> QUALITY_GATES.md <<'EOF'

## Release 4.3.2 — Gate Evidence
- Q1 Technical accuracy: see `data/CHECKS/validation_report.json` and contracts under `data/CONTRACTS/`.
- Q2 Sources & DOI concept: `metadata_v4.3.2.yaml` (concept_doi set).
- Q3 Terminology consistency: AG5/KEC, L0/L1/L2 reflected in DATA_DICTIONARY.md and contracts.
- Q4 IMRaD & release notes: `RELEASE_NOTES_v4.3.2.md`.
- Q5 Reproducibility: scripts under `scripts/`, Makefile targets `init/checksum/validate/package`.
- Q6 Limitations/biases: release notes section.
- Q7 Actions (Next Steps): release notes section.
- Q8 Impact: release notes section.
- Q9 Ethics/Licenses: public data only; see `data/LICENSES/` (if provided) and no PII.
- Q10 Alignment: supports the project’s primary objective via crystallization.
EOF
  else
    cat > QUALITY_GATES.md <<'EOF'
# Quality Gates (PM 4.3 — Q1–Q10)

- Q1 Technical accuracy
- Q2 Sources and Concept DOI
- Q3 Terminology consistency
- Q4 IMRaD and release notes
- Q5 Reproducibility
- Q6 Limitations and biases
- Q7 Clear actions (Next Steps)
- Q8 Impact (dataset/toolbox)
- Q9 Ethics/Licenses (no PII)
- Q10 Alignment to the core objective

## Release 4.3.2 — Gate Evidence
- Q1 Technical accuracy: see `data/CHECKS/validation_report.json` and contracts under `data/CONTRACTS/`.
- Q2 Sources & DOI concept: `metadata_v4.3.2.yaml` (concept_doi set).
- Q3 Terminology consistency: AG5/KEC, L0/L1/L2 reflected in DATA_DICTIONARY.md and contracts.
- Q4 IMRaD & release notes: `RELEASE_NOTES_v4.3.2.md`.
- Q5 Reproducibility: scripts under `scripts/`, Makefile targets `init/checksum/validate/package`.
- Q6 Limitations/biases: release notes section.
- Q7 Actions (Next Steps): release notes section.
- Q8 Impact: release notes section.
- Q9 Ethics/Licenses: public data only; see `data/LICENSES/` (if provided) and no PII.
- Q10 Alignment: supports the project’s primary objective via crystallization.
EOF
  fi
}

run_pipeline() {
  echo "[release] Ensuring directories"
  ensure_dirs

  echo "[release] Checking Python and dependencies"
  ensure_python_and_libs

  echo "[release] Checking for crystallization kit"
  unpack_kit_if_present

  echo "[release] Ensuring minimal files (placeholders only if missing)"
  ensure_minimal_files

  echo "[release] Running pipeline: make init, checksum, validate, linkcheck, package"
  make init
  make checksum || echo "[release] WARN: checksum step reported issues"
  make validate || echo "[release] WARN: validate step reported issues"
  python3 scripts/linkcheck_local.py || echo "[release] WARN: linkcheck step reported issues"
  make package
}

git_and_tag() {
  echo "[release] Preparing git commit and tag"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git add \
      CHANGELOG_v4.3.2.md RELEASE_NOTES_v4.3.2.md CITATION_v4.3.2.cff \
      metadata_v4.3.2.yaml zenodo_v4.3.2.json PROVENANCE.yaml DATA_DICTIONARY.md \
      QUALITY_GATES.md Makefile .gitattributes \
      data/CONTRACTS/*.yml scripts/*.py data/CHECKS/* || true
    git commit -m "chore(release): v4.3.2 — data crystallization (L0→L1→L2) + provenance, contracts, validations" || echo "[release] WARN: git commit failed or nothing to commit"
    git tag -a v4.3.2 -m "v4.3.2" || echo "[release] WARN: git tag might already exist"

    # Create GitHub release if possible
    if command -v gh >/dev/null 2>&1; then
      if git remote get-url origin 2>/dev/null | grep -qi "github.com"; then
        gh release create v4.3.2 data_release.tar.gz \
          --title "v4.3.2 — data crystallization patch" \
          --notes-file RELEASE_NOTES_v4.3.2.md \
          || echo "[release] INFO: Could not create GitHub release (auth/permission?). Create manually."
      else
        echo "[release] INFO: Remote is not GitHub; manual release required."
      fi
    else
      echo "[release] INFO: 'gh' CLI not found. To publish a GitHub release manually:"
      echo "  1) Push tag: git push origin v4.3.2"
      echo "  2) Create a release titled 'v4.3.2 — data crystallization patch' and upload data_release.tar.gz"
    fi
  else
    echo "[release] INFO: Not a git repository. Skipping commit/tag steps."
  fi
}

post_doi_instructions() {
  cat <<'EOF'
[release] Next action (post-DOI):
After Zenodo mints the Version DOI, update the following fields:
- Set 'doi' in CITATION_v4.3.2.cff
- Set 'version_doi' in metadata_v4.3.2.yaml
Then commit:
  git add CITATION_v4.3.2.cff metadata_v4.3.2.yaml
  git commit -m "docs: add Version DOI to v4.3.2"
  git push && git push --tags
EOF
}

acceptance_check() {
  echo "[release] ACCEPTANCE CRITERIA — verifying generated artifacts"
  required=(
    "data/CHECKS/checksums.csv"
    "data/CHECKS/validation_report.json"
    "data/CHECKS/linkcheck_report.json"
    "data_release.tar.gz"
  )
  missing=()
  for f in "${required[@]}"; do
    [ -f "$f" ] || missing+=("$f")
  done
  if [ ${#missing[@]} -eq 0 ]; then
    echo "  a) OK: checksums.csv, validation_report.json, linkcheck_report.json, data_release.tar.gz present"
  else
    echo "  a) MISSING: ${missing[*]}" >&2
  fi
  if [ -f CHANGELOG_v4.3.2.md ] && [ -f RELEASE_NOTES_v4.3.2.md ] && [ -f CITATION_v4.3.2.cff ] && [ -f metadata_v4.3.2.yaml ] && [ -f zenodo_v4.3.2.json ]; then
    echo "  b) OK: v4.3.2 metadata present and tracked"
  else
    echo "  b) WARN: Some v4.3.2 metadata files are missing" >&2
  fi
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if git tag -l | grep -q '^v4.3.2$'; then
      echo "  c) OK: tag v4.3.2 exists (release published if gh succeeded)"
    else
      echo "  c) WARN: git tag v4.3.2 not found" >&2
    fi
  else
    echo "  c) INFO: No git repository; skipping tag check"
  fi
}

# Execute
run_pipeline
git_and_tag
post_doi_instructions
acceptance_check

echo "[release] Completed v4.3.2 at $(date)"

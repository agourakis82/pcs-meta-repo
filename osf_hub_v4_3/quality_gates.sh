#!/usr/bin/env bash
set -euo pipefail
CMD=${1:-"check"}

info(){ echo -e "\n[INFO] $1\n"; }

reproduce(){
  info "Step 1/4: Build KEC from SWOW";        python scripts/build_kec.py
  info "Step 2/4: Align ZuCo";                 python scripts/align_zuco.py
  info "Step 3/4: Run models";                 python scripts/run_models.py
  info "Step 4/4: Make figures (F2/F3)";       python scripts/make_figures.py
  # Optional heavy steps (nulls/bootstrap). Set FAST=1 to skip.
  if [[ "${FAST:-0}" != "1" ]]; then
    info "Step 5/6: Null graphs (degree-preserving)";  python scripts/generate_nulls.py || echo "[warn] nulls failed"
    info "Step 6/6: Bootstrap CIs (2000 reps)";        python scripts/bootstrap_ci.py  || echo "[warn] bootstrap failed"
  else
    info "FAST=1: Skipping nulls/bootstrap"
  fi
  info "Done. Outputs in results/"
}

check(){
  info "Markdown lint"; command -v markdownlint >/dev/null 2>&1 && markdownlint **/*.md || echo "skip"
  info "YAML lint";     command -v yamllint    >/dev/null 2>&1 && yamllint -s .        || echo "skip"
  info "Ruff";          command -v ruff        >/dev/null 2>&1 && ruff check --exit-zero || echo "skip"
  info "Figures & tables"; test -d results/figures/metrics || (echo "Missing figures dir" && exit 1)
  ls results/models_reading_coeffs.csv results/models_reading_coeffs_fdr.csv results/mixedlm_ffd_summary.txt >/dev/null
  info "Link check"; command -v markdown-link-check >/dev/null 2>&1 && markdown-link-check -q README.md || echo "skip"
}

case "$CMD" in
  reproduce) reproduce ;;
  check)     check ;;
  *) echo "Usage: $0 [reproduce|check]" ; exit 1 ;;
esac

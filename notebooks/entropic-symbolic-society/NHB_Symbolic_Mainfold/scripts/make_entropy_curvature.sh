#!/usr/bin/env bash
# make_entropy_curvature.sh
# Batch runner for compute_entropy_curvature.py using a simple CSV job list or defaults.
# Requires: python3, networkx; optional GraphRicciCurvature for kappa.
#
# USAGE
#   ./make_entropy_curvature.sh                 # run default job on word_network.graphml
#   ./make_entropy_curvature.sh jobs.csv        # run jobs from CSV (graph,regime,betas,curv_undirected,out)
#
# CSV FORMAT (header required):
# graph,regime,betas,curv_undirected,out
# NHB_Symbolic_Mainfold/data/word_network.graphml,baseline,"0.5 0.8 1.0 1.2 1.5 2.0",false,entropy_curvature_baseline.csv
# runs/sim_disconnection.graphml,selective,"0.8 1.0 1.2",true,entropy_curvature_selective.csv
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${HERE}/compute_entropy_curvature.py"

if [[ ! -f "${PY}" ]]; then
  echo "ERROR: compute_entropy_curvature.py not found next to this script." >&2
  exit 2
fi

JOBS="${1:-}"
OUT_ALL="${2:-entropy_curvature_all.csv}"

run_job () {
  local graph="$1"
  local regime="$2"
  local betas="$3"
  local curv="$4"
  local out="$5"

  if [[ ! -f "$graph" ]]; then
    echo "WARN: graph not found: $graph — skipping" >&2
    return
  fi

  echo ">> computing: graph=$graph regime=$regime betas=[$betas] curv_undirected=$curv -> $out"
  if [[ "$curv" == "true" ]]; then
    python3 "${PY}" --graph "$graph" --beta $betas --curv-undirected --regime "$regime" --out "$out"
  else
    python3 "${PY}" --graph "$graph" --beta $betas --regime "$regime" --out "$out"
  fi
}

if [[ -z "${JOBS}" ]]; then
  # default single job
  DEFAULT_GRAPH="NHB_Symbolic_Mainfold/data/word_network.graphml"
  DEFAULT_OUT="entropy_curvature_baseline.csv"
  run_job "$DEFAULT_GRAPH" "baseline" "0.5 0.8 1.0 1.2 1.5 2.0" "false" "$DEFAULT_OUT"
  cat "$DEFAULT_OUT" > "$OUT_ALL"
  echo "Wrote $OUT_ALL"
  exit 0
fi

if [[ ! -f "$JOBS" ]]; then
  echo "ERROR: jobs file not found: $JOBS" >&2
  exit 3
fi

# Read CSV (skip header)
TMP_OUTS=()
tail -n +2 "$JOBS" | while IFS=, read -r graph regime betas curv out; do
  # strip quotes
  betas="${betas%\"}"; betas="${betas#\"}"
  run_job "$graph" "$regime" "$betas" "$curv" "$out"
  TMP_OUTS+=("$out")
done

# concatenate all into OUT_ALL with unique header
{
  head -n 1 "$(ls -1 *.csv | head -n1)"
  for f in *.csv; do
    tail -n +2 "$f" || true
  done
} > "$OUT_ALL"

echo "Wrote $OUT_ALL"

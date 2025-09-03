#!/usr/bin/env bash
set -euo pipefail
NODE="${OSF_NODE:-2aqp7}"

command -v osf >/dev/null 2>&1 || {
  command -v pipx >/dev/null 2>&1 && pipx install osfclient || pip install --user osfclient
}

# Determine auth args (optional)
USER_OPT=()
if [[ -n "${OSF_USERNAME:-}" ]]; then
  USER_OPT=(-u "$OSF_USERNAME")
fi

# Ensure credentials are available (config or env)
if [[ ! -f "$HOME/.osfcli.config" && -z "${OSF_PASSWORD:-}" && -z "${OSF_USERNAME:-}" ]]; then
  echo "[ERROR] osfclient not configured. Run 'osf init' (interactive) or export OSF_USERNAME and OSF_PASSWORD, then retry." >&2
  exit 2
fi

# Upload root files
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/README_for_PIs.md /README_for_PIs.md
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/PREREGISTRATION.md /PREREGISTRATION.md
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/OSF_WIKI.md /OSF_WIKI.md
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/REPRODUCE.md /REPRODUCE.md
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/provenance.yaml /provenance.yaml
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/environment.yml /environment.yml
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/quality_gates.sh /quality_gates.sh
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/LICENSE.txt /LICENSE.txt
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/CITATION.cff /CITATION.cff

# Ensure results folders exist (placeholders)
touch osf_hub_v4_3/results/.gitkeep osf_hub_v4_3/results/figures/metrics/.gitkeep
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/results/.gitkeep /results/.gitkeep
osf "${USER_OPT[@]}" -p "$NODE" upload -f osf_hub_v4_3/results/figures/metrics/.gitkeep /results/figures/metrics/.gitkeep

# Upload minimal results bundle if present
upload_if_exists(){
  local SRC="$1"; local DST="$2"
  if [[ -f "$SRC" ]]; then
    osf "${USER_OPT[@]}" -p "$NODE" upload -f "$SRC" "$DST"
  else
    echo "[skip] $SRC (missing)"
  fi
}

upload_if_exists osf_hub_v4_3/results/models_reading_coeffs.csv        /results/models_reading_coeffs.csv
upload_if_exists osf_hub_v4_3/results/models_reading_coeffs_fdr.csv    /results/models_reading_coeffs_fdr.csv
upload_if_exists osf_hub_v4_3/results/mixedlm_ffd_summary.txt          /results/mixedlm_ffd_summary.txt
upload_if_exists osf_hub_v4_3/results/figures/metrics/F2_.png          /results/figures/metrics/F2_.png
upload_if_exists osf_hub_v4_3/results/figures/metrics/F3_.png          /results/figures/metrics/F3_.png
upload_if_exists osf_hub_v4_3/results/kec_metrics.csv                  /results/kec_metrics.csv
upload_if_exists osf_hub_v4_3/results/zuco_aligned.csv                 /results/zuco_aligned.csv

echo "[OK] Uploaded OSF hub files to node $NODE."

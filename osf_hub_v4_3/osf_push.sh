#!/usr/bin/env bash
set -euo pipefail
NODE="${OSF_NODE:-2aqp7}"

command -v osf >/dev/null 2>&1 || {
  command -v pipx >/dev/null 2>&1 && pipx install osfclient || pip install --user osfclient
}

# Upload root files
osf -p "$NODE" upload -f osf_hub_v4_3/README_for_PIs.md /README_for_PIs.md
osf -p "$NODE" upload -f osf_hub_v4_3/PREREGISTRATION.md /PREREGISTRATION.md
osf -p "$NODE" upload -f osf_hub_v4_3/OSF_WIKI.md /OSF_WIKI.md
osf -p "$NODE" upload -f osf_hub_v4_3/REPRODUCE.md /REPRODUCE.md
osf -p "$NODE" upload -f osf_hub_v4_3/provenance.yaml /provenance.yaml
osf -p "$NODE" upload -f osf_hub_v4_3/environment.yml /environment.yml
osf -p "$NODE" upload -f osf_hub_v4_3/quality_gates.sh /quality_gates.sh
osf -p "$NODE" upload -f osf_hub_v4_3/LICENSE.txt /LICENSE.txt
osf -p "$NODE" upload -f osf_hub_v4_3/CITATION.cff /CITATION.cff

# Ensure results folders exist (placeholders)
touch osf_hub_v4_3/results/.gitkeep osf_hub_v4_3/results/figures/metrics/.gitkeep
osf -p "$NODE" upload -f osf_hub_v4_3/results/.gitkeep /results/.gitkeep
osf -p "$NODE" upload -f osf_hub_v4_3/results/figures/metrics/.gitkeep /results/figures/metrics/.gitkeep
echo "[OK] Uploaded OSF hub files to node $NODE."


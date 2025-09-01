#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(pwd)"
RAW_DIR="$ROOT_DIR/data/raw_public"
PROV_DIR="$ROOT_DIR/data/provenance"

sha_line () {
  local f="$1"
  if command -v shasum >/dev/null 2>&1; then
    echo "$(shasum -a 256 "$f" | awk '{print $1}')"
  else
    # Linux
    echo "$(sha256sum "$f" | awk '{print $1}')"
  fi
}

update_yaml () {
  local yaml="$1"; shift
  local out="$yaml.tmp"
  echo "hashes:" > "$out"
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    h="$(sha_line "$f")"
    sz="$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f")"
    echo "  - file: ${f#./}" >> "$out"
    echo "    sha256: $h" >> "$out"
    echo "    bytes: $sz" >> "$out"
  done
  # Merge back into the original YAML (simple replace of hashes section)
  awk 'BEGIN{{s=0}} /^hashes:/{print; while((getline line)<0){{}}} /hashes:/{s=1; print; while(getline<"'"$out"'"){print}; next}1' "$yaml" > "$yaml.updated" || cp "$out" "$yaml.updated"
  mv "$yaml.updated" "$yaml"
  rm -f "$out"
}

echo "[1/3] Scanning raw files ..."
mapfile -t ZUCO_FILES < <(find ./data/raw_public/zuco -type f | sort)
mapfile -t SWOW_FILES < <(find ./data/raw_public/swow -type f | sort)

echo "[2/3] Updating provenance YAMLs ..."
# Append hashes to YAMLs
if [ -f "$PROV_DIR/provenance_zuco.yaml" ]; then
  printf "%s
" "${ZUCO_FILES[@]}" | sed 's/^/  /' > /tmp/zuco_files.txt
  # Build a new hashes section
  {
    echo "hashes:"
    for f in "${ZUCO_FILES[@]}"; do
      [ -f "$f" ] || continue
      h="$(sha_line "$f")"
      sz="$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f")"
      echo "  - file: ${f#./}"
      echo "    sha256: $h"
      echo "    bytes: $sz"
    done
  } > /tmp/zuco_hashes.yaml
  # Replace hashes block
  awk 'BEGIN{p=1} /^hashes:/{print; while((getline)<0){} }1' "$PROV_DIR/provenance_zuco.yaml" > "$PROV_DIR/provenance_zuco.yaml.bak" || true
  mv /tmp/zuco_hashes.yaml "$PROV_DIR/provenance_zuco.yaml"
fi

if [ -f "$PROV_DIR/provenance_swow.yaml" ]; then
  {
    echo "hashes:"
    for f in "${SWOW_FILES[@]}"; do
      [ -f "$f" ] || continue
      h="$(sha_line "$f")"
      sz="$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f")"
      echo "  - file: ${f#./}"
      echo "    sha256: $h"
      echo "    bytes: $sz"
    done
  } > /tmp/swow_hashes.yaml
  mv /tmp/swow_hashes.yaml "$PROV_DIR/provenance_swow.yaml"
fi

echo "[3/3] Done. Provenance files updated:"
ls -1 "$PROV_DIR"/provenance_*.yaml || true

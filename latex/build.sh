#!/usr/bin/env bash
set -euo pipefail

# Compile LaTeX documents in this repo.
# Usage:
#   bash latex/build.sh                # build detected main .tex files
#   bash latex/build.sh all            # same as above
#   bash latex/build.sh <path/to.tex>  # build a specific file

HERE_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$HERE_DIR/.." && pwd)
BIN_DIR="$REPO_ROOT/tools/bin"
mkdir -p "$BIN_DIR"

log() { printf '[latex] %s\n' "$*"; }
warn() { printf '[latex][WARN] %s\n' "$*" 1>&2; }
die() { printf '[latex][ERROR] %s\n' "$*" 1>&2; exit 1; }

# Find or install a Tectonic binary locally (no root required).
ensure_tectonic() {
  if command -v tectonic >/dev/null 2>&1; then
    printf '%s' "tectonic"
    return
  fi
  if [ -x "$BIN_DIR/tectonic" ]; then
    printf '%s' "$BIN_DIR/tectonic"
    return
  fi

  log "Tectonic not found; attempting local download (Linux x86_64)..."
  TMPDIR=$(mktemp -d)
  # Discover latest release asset dynamically from GitHub API (no auth)
  API_URL="https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest"
  if command -v curl >/dev/null 2>&1; then
    ASSET_URL=$(curl -fsSL "$API_URL" | grep -oE '"browser_download_url"\s*:\s*"[^"]+x86_64-unknown-linux-gnu\.tar\.gz"' | head -n1 | sed -E 's/.*"(http[^"]+)"/\1/') || true
  else
    ASSET_URL=$(wget -qO- "$API_URL" | grep -oE '"browser_download_url"\s*:\s*"[^"]+x86_64-unknown-linux-gnu\.tar\.gz"' | head -n1 | sed -E 's/.*"(http[^"]+)"/\1/') || true
  fi
  [ -n "${ASSET_URL:-}" ] || die "Could not determine Tectonic asset URL"
  log "Downloading: $ASSET_URL"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$ASSET_URL" -o "$TMPDIR/tectonic.tar.gz" || die "Failed to download Tectonic tarball"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TMPDIR/tectonic.tar.gz" "$ASSET_URL" || die "Failed to download Tectonic tarball"
  else
    die "Need curl or wget to download Tectonic"
  fi

  tar -xzf "$TMPDIR/tectonic.tar.gz" -C "$TMPDIR" || die "Failed to extract Tectonic"
  # Find the binary inside the extracted directory
  TTK_BIN=$(find "$TMPDIR" -type f -name tectonic -perm -u+x | head -n 1 || true)
  [ -n "$TTK_BIN" ] || die "Tectonic binary not found in archive"
  install -m 0755 "$TTK_BIN" "$BIN_DIR/tectonic" || die "Failed to install Tectonic to $BIN_DIR"
  rm -rf "$TMPDIR"
  printf '%s' "$BIN_DIR/tectonic"
}

prepare_assets() {
  # 1) Provide PNG placeholders for MDPI logos if EPS exists
  local defs_dir="$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions"
  if [ -d "$defs_dir" ]; then
    for base in logo-mdpi logo-mdpi-ijom logo-mdpi-siuj logo-mdpi-scipharm; do
      if [ -f "$defs_dir/${base}.eps" ]; then
        # Always ensure a small valid PNG placeholder exists
        rm -f "$defs_dir/${base}.png" 2>/dev/null || true
        log "Ensuring placeholder ${base}.png"
        DEFS_DIR="$defs_dir" PNG_NAME="${base}.png" python - << 'PY'
import base64,sys,os
png_b64 = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/xcAAuMBg1XCM0oAAAAASUVORK5CYII="
defs = os.environ['DEFS_DIR']
name = os.environ['PNG_NAME']
with open(os.path.join(defs,name),'wb') as f:
    f.write(base64.b64decode(png_b64))
PY
      fi
    done
  fi

  # 2) Ensure mdpi class is reachable in paper_model via symlink
  local pm_dir="$REPO_ROOT/papers/fractal-entropy-project/paper_model"
  if [ -d "$pm_dir" ]; then
    if [ ! -f "$pm_dir/mdpi.cls" ]; then
      ln -sf "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/mdpi.cls" "$pm_dir/mdpi.cls" || true
    fi
    if [ ! -f "$pm_dir/mdpi.bst" ] && [ -f "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/mdpi.bst" ]; then
      ln -sf "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/mdpi.bst" "$pm_dir/mdpi.bst" || true
    fi
    # Provide required Definitions assets expected by mdpi.cls
    if [ ! -d "$pm_dir/Definitions" ]; then
      mkdir -p "$pm_dir/Definitions"
    fi
    for f in journalnames.tex; do
      if [ -f "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/$f" ] && [ ! -f "$pm_dir/Definitions/$f" ]; then
        ln -sf "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/$f" "$pm_dir/Definitions/$f" || true
      fi
    done
    # Link placeholder MDPI logo
    if [ -f "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/logo-mdpi.png" ] && [ ! -f "$pm_dir/Definitions/logo-mdpi.png" ]; then
      ln -sf "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions/logo-mdpi.png" "$pm_dir/Definitions/logo-mdpi.png" || true
    fi
  fi

  # 3) Convert any EPS logos to PDF/PNG if tools available
  convert_eps_dir() {
    local d="$1"
    [ -d "$d" ] || return 0
    for eps in "$d"/*.eps; do
      [ -f "$eps" ] || continue
      local base=${eps%.eps}
      if command -v gs >/dev/null 2>&1; then
        # PDF conversion
        if [ ! -f "$base.pdf" ]; then
          log "Converting $(basename "$eps") -> $(basename "$base.pdf")"
          gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile="$base.pdf" "$eps" >/dev/null 2>&1 || true
        fi
        # PNG conversion
        if [ ! -f "$base.png" ]; then
          log "Converting $(basename "$eps") -> $(basename "$base.png")"
          gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha -r300 -sOutputFile="$base.png" "$eps" >/dev/null 2>&1 || true
        fi
      elif command -v convert >/dev/null 2>&1; then
        [ -f "$base.pdf" ] || convert "$eps" "$base.pdf" >/dev/null 2>&1 || true
        [ -f "$base.png" ] || convert -density 300 "$eps" "$base.png" >/dev/null 2>&1 || true
      else
        warn "EPS found in $d but no converter (ghostscript/convert) available"
      fi
    done
  }
  convert_eps_dir "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/Definitions"
  convert_eps_dir "$pm_dir/Definitions"
}

is_tex_main() {
  # Heuristic: a main file contains \documentclass or \begin{document}
  grep -qE "\\\documentclass|\\\begin\{document\}" "$1"
}

discover_tex_mains() {
  # Search for .tex files that look like mains; avoid common include dirs
  grep -R --include='*.tex' -IlZ "\\begin{document}" "$REPO_ROOT" 2>/dev/null \
    | tr '\0' '\n' \
    | grep -Ev \
      "/(sections|appendices|figures|tables|Definitions|code|templates|includes)/" \
    || true
}

build_with_tectonic() {
  local tectonic_bin="$1"; shift
  local texfile="$1"; shift
  local dir base
  dir=$(dirname "$texfile")
  base=$(basename "$texfile")
  (
    cd "$dir"
    log "Compiling $texfile"
    # Try new CLI first, then fallback to legacy invocation
    if "$tectonic_bin" -X compile "$base" -Z shell-escape; then
      log "✓ Success: $texfile"
      return 0
    fi
    if "$tectonic_bin" "$base"; then
      log "✓ Success (legacy): $texfile"
      return 0
    fi
    warn "Failed to compile with Tectonic: $texfile"
    return 1
  )
}

main() {
  local targets=()
  if [ $# -gt 0 ] && [ "$1" != "all" ]; then
    targets=("$1")
  else
    mapfile -t targets < <(discover_tex_mains)
    # Fallback to curated list if discovery returns nothing
    if [ ${#targets[@]} -eq 0 ]; then
      targets=(
        "$REPO_ROOT/preprint_skeleton.tex"
        "$REPO_ROOT/papers/fractal-entropy-project/paper_model/main.tex"
        "$REPO_ROOT/papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/main.tex"
        "$REPO_ROOT/notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/Main_sr.tex"
        "$REPO_ROOT/notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/NHB_main.tex"
      )
    fi
  fi

  # Filter to files that exist and look like mains
  local mains=()
  for f in "${targets[@]}"; do
    [ -f "$f" ] || continue
    if is_tex_main "$f"; then mains+=("$f"); fi
  done
  [ ${#mains[@]} -gt 0 ] || die "No LaTeX main files found to build"

  local tectonic_bin
  tectonic_bin=$(ensure_tectonic)
  log "Using $("$tectonic_bin" --version 2>/dev/null || echo tectonic)"
  prepare_assets

  local ok=0 fail=0
  for f in "${mains[@]}"; do
    if build_with_tectonic "$tectonic_bin" "$f"; then
      ok=$((ok+1))
    else
      fail=$((fail+1))
    fi
  done

  log "Build summary: ${ok} succeeded, ${fail} failed"
  [ "$fail" -eq 0 ] || exit 2
}

main "$@"

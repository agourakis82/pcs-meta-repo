#!/usr/bin/env bash
# reset_env.sh — Create a clean, reproducible environment and install dependencies.
# Usage:
#   bash scripts/reset_env.sh [ENV_NAME] [PYTHON_VERSION]
# Defaults:
#   ENV_NAME="entropic-symbolic-mainfold"
#   PYTHON_VERSION="3.11"
#
# Prefers Conda if available; falls back to Python venv otherwise.
# Installs dependencies from requirements.txt and ensures JupyterLab is present.

set -Eeuo pipefail

ENV_NAME="${1:-entropic-symbolic-mainfold}"
PY_VERSION="${2:-3.11}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQ_FILE="$ROOT_DIR/requirements.txt"

echo "[INFO] Project root: $ROOT_DIR"
echo "[INFO] Target environment: $ENV_NAME (Python $PY_VERSION)"
echo "[INFO] Requirements file: $REQ_FILE"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "[ERROR] requirements.txt not found at $REQ_FILE"
  exit 1
fi

have_conda() {
  command -v conda >/dev/null 2>&1
}

if have_conda; then
  echo "[INFO] Conda detected. Creating environment '$ENV_NAME' with Python $PY_VERSION ..."
  conda create -y -n "$ENV_NAME" "python=$PY_VERSION"
  echo "[INFO] Installing requirements into '$ENV_NAME' ..."
  conda run -n "$ENV_NAME" python -m pip install --upgrade pip
  conda run -n "$ENV_NAME" python -m pip install -r "$REQ_FILE"
  conda run -n "$ENV_NAME" python - <<'PY'
import importlib, sys, subprocess
try:
    importlib.import_module("jupyterlab")
    print("[INFO] jupyterlab already available.")
except ImportError:
    print("[INFO] Installing jupyterlab ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jupyterlab"])
PY
  echo "[DONE] Conda environment '$ENV_NAME' ready."
  echo "[TIP] Activate with: conda activate $ENV_NAME"
  echo "[TIP] Launch JupyterLab with: jupyter lab"
else
  echo "[WARN] Conda not detected. Falling back to python venv in .venv/"
  cd "$ROOT_DIR"
  PYTHON_BIN="$(command -v python3 || command -v python)"
  if [[ -z "$PYTHON_BIN" ]]; then
    echo "[ERROR] Could not find a Python interpreter in PATH."
    exit 1
  fi
  echo "[INFO] Using Python at: $PYTHON_BIN"
  "$PYTHON_BIN" -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r "$REQ_FILE"
  python - <<'PY'
import importlib, sys, subprocess
try:
    importlib.import_module("jupyterlab")
    print("[INFO] jupyterlab already available.")
except ImportError:
    print("[INFO] Installing jupyterlab ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jupyterlab"])
PY
  echo "[DONE] Virtual environment '.venv' ready."
  echo "[TIP] Activate with: source .venv/bin/activate"
  echo "[TIP] Launch JupyterLab with: jupyter lab"
fi

echo "[NOTE] Optional extras: pip install umap-learn node2vec"

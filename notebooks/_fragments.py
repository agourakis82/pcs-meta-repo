from pathlib import Path
import json, sys, platform, pandas as pd, numpy as np
from IPython.display import HTML, display

def apply_style():
    css = Path("notebooks/_style.css")
    if css.exists():
        display(HTML(f"<style>{css.read_text()}</style>"))
    else:
        print("[STYLE] _style.css not found; proceeding.")

def preflight_checks():
    print("[Preflight] Python:", sys.version.split()[0],
          "| Platform:", platform.platform())
    print("[Preflight] pandas:", pd.__version__, "| numpy:", np.__version__)
    for p in ["data", "data/processed", "reports", "figures/metrics"]:
        Path(p).mkdir(parents=True, exist_ok=True)
    print("[Preflight] Folders ready.")

def print_contract():
    msg = """
**Notebook Contract (PCS‑HELIO v4.3)**
- IMRaD sections (Intro/Methods/Results/Discussion).
- RUN_MODE ∈ {'sample','full'}; sample must run fast and never crash.
- Required outputs saved under data/processed/** and reports/**.
- QA cell with asserts (columns present, row counts, coverage).
- Seeds fixed; no absolute paths; public data only.
"""
    display(HTML(f"<pre>{msg}</pre>"))

def qa_assertions(df: pd.DataFrame, rules: dict):
    assert isinstance(df, pd.DataFrame) and len(df) > 0, "Empty DataFrame."
    if "required_cols" in rules:
        missing = [c for c in rules["required_cols"] if c not in df.columns]
        assert not missing, f"Missing required cols: {missing}"
    if "min_rows" in rules:
        assert len(df) >= rules["min_rows"], f"Too few rows (<{rules['min_rows']})."
    print("[QA] Basic checks passed.")

def save_manifest(path: str | Path, payload: dict):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[MANIFEST] Wrote {p}")

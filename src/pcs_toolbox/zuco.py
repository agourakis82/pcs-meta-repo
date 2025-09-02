from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

CANON_KEYS = ["Dataset","Task","Subject","SentenceID","w_pos","token","token_norm"]
ET_COLS = ["FFD","GD","TRT","GPT"]
EEG_COLS = ["theta1","alpha1","beta1","gamma1"]


def token_norm(s: Optional[str]) -> Optional[str]:
    if s is None or not isinstance(s, str):
        return s
    import re
    return re.sub(r"[\W_]+", "", s.lower())


@dataclass
class Discovery:
    et_mat: List[Path]
    eeg_tabular: List[Path]


def discover(base: Path) -> Dict[str, Discovery]:
    out: Dict[str, Discovery] = {}
    for v in ["v1","v2"]:
        root = base / v
        if not root.exists():
            out[v] = Discovery(et_mat=[], eeg_tabular=[])
            continue
        et_mat = sorted(root.rglob("*_corrected_ET.mat"))
        eeg_tab = sorted([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv",".tsv",".txt"}])
        out[v] = Discovery(et_mat=et_mat, eeg_tabular=eeg_tab)
    return out


def load_et(base: Path) -> pd.DataFrame:
    """Placeholder: defer to tools.zuco_loader existing implementation.
    Here we route to that module to keep a single source of truth.
    """
    import importlib.util, sys
    # Find repo root by looking for README.md or pyproject.toml
    repo_root = None
    for p in [base, *base.parents]:
        if (p / 'README.md').exists() or (p / 'pyproject.toml').exists():
            repo_root = p
            break
    repo_root = repo_root or base.parents[2]
    loader_path = (repo_root / 'tools' / 'zuco_loader.py').resolve()
    spec = importlib.util.spec_from_file_location('zuco_loader', loader_path)
    assert spec is not None and spec.loader is not None
    zuco_loader = importlib.util.module_from_spec(spec)
    sys.modules['zuco_loader'] = zuco_loader
    spec.loader.exec_module(zuco_loader)
    return zuco_loader.load_et(base, n_jobs=1)


def load_eeg(base: Path) -> pd.DataFrame:
    import importlib.util, sys
    repo_root = None
    for p in [base, *base.parents]:
        if (p / 'README.md').exists() or (p / 'pyproject.toml').exists():
            repo_root = p
            break
    repo_root = repo_root or base.parents[2]
    loader_path = (repo_root / 'tools' / 'zuco_loader.py').resolve()
    spec = importlib.util.spec_from_file_location('zuco_loader', loader_path)
    assert spec is not None and spec.loader is not None
    zuco_loader = importlib.util.module_from_spec(spec)
    sys.modules['zuco_loader'] = zuco_loader
    spec.loader.exec_module(zuco_loader)
    return zuco_loader.load_eeg(base)


def merge_et_eeg(et: pd.DataFrame, eeg: pd.DataFrame) -> pd.DataFrame:
    import importlib.util, sys
    # Delegate to tools.merge to reuse hardened logic
    # Resolve repo root from CWD
    cwd = Path.cwd()
    repo_root = None
    for p in [cwd, *cwd.parents]:
        if (p / 'README.md').exists() or (p / 'pyproject.toml').exists():
            repo_root = p
            break
    repo_root = repo_root or cwd
    loader_path = (repo_root / 'tools' / 'zuco_loader.py').resolve()
    spec = importlib.util.spec_from_file_location('zuco_loader', loader_path)
    assert spec is not None and spec.loader is not None
    zuco_loader = importlib.util.module_from_spec(spec)
    sys.modules['zuco_loader'] = zuco_loader
    spec.loader.exec_module(zuco_loader)
    return zuco_loader.merge_et_eeg(et, eeg)


def load_all(raw_base: Path, write_outputs: bool = True) -> pd.DataFrame:
    et = load_et(raw_base)
    eeg = load_eeg(raw_base)
    merged = merge_et_eeg(et, eeg)
    if write_outputs:
        proc = raw_base.parents[1] / 'processed'
        proc.mkdir(parents=True, exist_ok=True)
        out_csv = proc / 'zuco_aligned.csv'
        merged.to_csv(out_csv, index=False)
        # QA JSON
        qa = {
            'rows': int(len(merged)),
            'et_coverage_pct': {c: f"{merged[c].notna().mean()*100:.1f}%" for c in ET_COLS if c in merged.columns},
            'eeg_coverage_pct': {c: f"{merged[c].notna().mean()*100:.1f}%" for c in EEG_COLS if c in merged.columns},
        }
        # reports at repo root
        repo_root = raw_base
        for p in [raw_base, *raw_base.parents]:
            if (p / 'README.md').exists() or (p / 'pyproject.toml').exists():
                repo_root = p
                break
        rpt = repo_root / 'reports'
        rpt.mkdir(parents=True, exist_ok=True)
        (rpt / 'zuco_loader_qa.json').write_text(pd.Series(qa).to_json(indent=2))
    return merged

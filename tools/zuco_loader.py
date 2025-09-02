"""
ZuCo v1+v2 loader utility
- Discovers ET/EEG files under data/raw_public/zuco/{v1,v2}
- Loads ET from MATLAB .mat (if scipy/h5py available) or tabular files when present
- Loads EEG from tabular files when present (theta/alpha/beta/gamma columns)
- Produces canonical schema keys and columns for downstream merge

Canonical keys:
  Dataset{v1|v2}, Task{NR|TSR}, Subject, SentenceID, w_pos, token, token_norm
Canonical columns:
  ET: FFD, GD, TRT, GPT
  EEG: theta1, alpha1, beta1, gamma1

Guardrails:
  - No absolute user paths; caller passes base path
  - Tolerate .csv/.tsv/.txt/.mat (skip with warning when unsupported)
  - Clear errors/warnings when required columns missing
  - English comments; consistent variable names
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import re
import warnings
import json

import numpy as np
import pandas as pd

try:
    from scipy.io import loadmat  # type: ignore
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

try:
    import h5py  # type: ignore
    _HAS_H5PY = True
except Exception:
    _HAS_H5PY = False

try:
    from joblib import Parallel, delayed  # type: ignore
    _HAS_JOBLIB = True
except Exception:
    _HAS_JOBLIB = False

# ----------------------- helpers -----------------------

def heartbeat(msg: str) -> None:
    print(f"[zuco_loader] {msg}")

def norm_token(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return re.sub(r"[\W_]+", "", s.lower())

def detect_task_from_path(p: Path) -> Optional[str]:
    # Task folder frequently contains 'task1 - NR' or 'task2 - TSR'
    for parent in p.parents:
        name = parent.name.lower()
        if 'task' in name:
            if 'nr' in name:
                return 'NR'
            if 'tsr' in name:
                return 'TSR'
    return None

@dataclass
class FileDiscovery:
    et_mat: List[Path]
    eeg_tabular: List[Path]

# ----------------------- discovery -----------------------

def discover(base_dir: Path) -> Dict[str, FileDiscovery]:
    """Discover ET/EEG files per dataset version below base_dir (which should be ../data/raw_public/zuco)."""
    results: Dict[str, FileDiscovery] = {}
    for version in ['v1', 'v2']:
        root = base_dir / version
        if not root.exists():
            heartbeat(f"WARN: missing {root}")
            results[version] = FileDiscovery(et_mat=[], eeg_tabular=[])
            continue
        et_mat = sorted(root.rglob('*_corrected_ET.mat'))
        # EEG: accept any csv/tsv/txt and let column mapping filter relevant files
        eeg_tabular = sorted([
            p for p in root.rglob('*')
            if p.is_file() and p.suffix.lower() in {'.csv', '.tsv', '.txt'}
        ])
        results[version] = FileDiscovery(et_mat=et_mat, eeg_tabular=eeg_tabular)
    return results

# ----------------------- ET from .mat -----------------------

def _find_wordbounds_file(version_path: Path, subject_id: str, session_id: str) -> Optional[Path]:
    candidates = list(version_path.rglob('wordbounds*.mat'))
    task_short = re.sub(r'\d+$', '', session_id)
    alt_ids = {session_id, session_id.replace('SR','SNR'), session_id.replace('SNR','SR')}
    patterns = set()
    for s in alt_ids:
        patterns.update({f"wordbounds_{s}.mat", f"wordbounds_{s}_{subject_id}.mat", f"wordbounds_{task_short}_{subject_id}.mat"})
    for f in candidates:
        if f.name in patterns:
            return f
    return None

def _get_v2_word_texts(version_path: Path, subject_id: str, task_folder_name: str) -> List[str]:
    # Token extraction from v2 HDF5 results is optional and brittle; skip in this version
    # to keep the loader robust across environments. Downstream uses token_norm when present.
    return []

def _process_session_from_mat_path(version_root: Path, et_path: Path) -> Optional[pd.DataFrame]:
    """Process a single ET .mat file given its absolute path.
    Supports both v1 (no task folder) and v2 (with task folder like 'task2 - TSR').
    """
    if not _HAS_SCIPY:
        heartbeat("WARN: scipy not available; skipping .mat ET")
        return None
    if not et_path.exists():
        return None
    m = re.match(r"(\w+)_(\w+)_corrected_ET\.mat", et_path.name)
    if not m:
        return None
    subject_id, session_id = m.groups()
    wb_path = _find_wordbounds_file(version_root, subject_id, session_id)
    if not wb_path:
        return None
    try:
        et_mat = loadmat(et_path, squeeze_me=True, struct_as_record=False)
        wb_mat = loadmat(wb_path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        heartbeat(f"WARN: loadmat failed for {et_path.name}/{wb_path.name}: {e}")
        return None

    eyedata = et_mat.get('eyeevent')
    wb_data = wb_mat.get('wordbounds')
    tb_data = wb_mat.get('textbounds')
    if eyedata is None or not hasattr(eyedata, 'fixations') or wb_data is None or tb_data is None:
        return None
    fix = eyedata.fixations.data if hasattr(eyedata.fixations, 'data') else eyedata.fixations
    if not isinstance(fix, np.ndarray) or fix.size == 0:
        return None

    version = version_root.name
    # Determine task: use session_id hint first, then parent folders
    sid_upper = session_id.upper()
    if 'NR' in sid_upper:
        task_short = 'NR'
    elif 'TSR' in sid_upper:
        task_short = 'TSR'
    else:
        task_short = detect_task_from_path(et_path) or ''

    # v2 tokens when possible
    tokens: List[str] = []
    if version == 'v2':
        task_folder = next((p.name for p in et_path.parents if 'task' in p.name.lower()), None)
        if task_folder:
            tokens = _get_v2_word_texts(version_root, subject_id, task_folder)

    rows: List[Dict] = []
    min_latency = np.min(fix[:, 0])
    global_w = 0
    for sent_idx, sent_data in enumerate(wb_data):
        # number of words in sentence
        if wb_data.dtype == 'O' and hasattr(sent_data, 'content'):
            n_words = len(sent_data.content)
        else:
            try:
                n_words = len(sent_data)
            except Exception:
                n_words = int(sent_data) if np.ndim(sent_data)==0 else 0
        if sent_idx >= len(tb_data) or n_words <= 0:
            continue
        sent_start, sent_end = tb_data[sent_idx][0], tb_data[sent_idx][1]
        duration = (sent_end - sent_start) / n_words if n_words > 0 else 0
        for w_pos in range(n_words):
            start_t = sent_start + (w_pos * duration) + min_latency
            end_t = start_t + duration
            # token text
            token = tokens[global_w] if version == 'v2' and global_w < len(tokens) else None
            mask = (fix[:, 0] >= start_t) & (fix[:, 0] < end_t)
            fseg = fix[mask]
            ffd = float(fseg[0, 2]) if len(fseg) > 0 else np.nan
            trt = float(np.sum(fseg[:, 2])) if len(fseg) > 0 else np.nan
            gd = float(np.sum(fseg[:-1, 2])) if len(fseg) > 1 else (ffd if not np.isnan(ffd) else np.nan)
            gpt = np.nan  # not derivable from fixations without regressions path; placeholder
            rows.append({
                'Dataset': version,
                'Task': task_short,
                'Subject': subject_id,
                'SentenceID': int(sent_idx+1),
                'w_pos': int(w_pos+1),
                'token': token,
                'token_norm': norm_token(token) if token else None,
                'FFD': ffd, 'GD': gd, 'TRT': trt, 'GPT': gpt,
            })
            global_w += 1
    if not rows:
        return None
    return pd.DataFrame(rows)

# ----------------------- EEG from tabular -----------------------

_EEG_NAME_MAP = {
    'theta': 'theta1', 'theta1': 'theta1', 'theta_power': 'theta1',
    'alpha': 'alpha1', 'alpha1': 'alpha1', 'alpha_power': 'alpha1',
    'beta': 'beta1', 'beta1': 'beta1', 'beta_power': 'beta1',
    'gamma': 'gamma1', 'gamma1': 'gamma1', 'gamma_power': 'gamma1',
}

_KEY_CANDIDATES = [
    ('Dataset',), ('Task',), ('Subject',), ('SentenceID','sentence','sentence_id'), ('w_pos','word_pos','position','w_idx'), ('token','word','token_text'), ('token_norm','word_norm','token_norm')
]

def _read_table_auto(path: Path) -> Optional[pd.DataFrame]:
    try:
        if path.suffix.lower() == '.csv':
            return pd.read_csv(path)
        if path.suffix.lower() == '.tsv':
            return pd.read_csv(path, sep='\t')
        if path.suffix.lower() == '.txt':
            # try comma then tab
            try:
                return pd.read_csv(path)
            except Exception:
                return pd.read_csv(path, sep='\t')
    except Exception as e:
        heartbeat(f"WARN: failed reading {path.name}: {e}")
        return None
    return None

def _map_eeg_columns(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    cols = {c: c for c in df.columns}
    # keys
    out = {}
    for choices in _KEY_CANDIDATES:
        present = [c for c in choices if c in df.columns]
        if present:
            out[choices[0]] = present[0]
    # minimally require Subject + some locator
    required_for_merge = ['Subject']
    if not all(k in out for k in required_for_merge):
        return None
    # map eeg cols
    eeg_cols = {}
    for c in df.columns:
        key = c.strip().lower()
        if key in _EEG_NAME_MAP:
            eeg_cols[c] = _EEG_NAME_MAP[key]
    if not eeg_cols:
        return None
    renamed = df.rename(columns={**{v:k for k,v in out.items()}, **eeg_cols})
    # ensure required canonical columns exist (fill when missing)
    for k in ['Dataset','Task','SentenceID','w_pos','token','token_norm']:
        if k not in renamed.columns:
            renamed[k] = np.nan
    # normalize token_norm if missing
    if 'token_norm' in renamed.columns and renamed['token_norm'].isna().any() and 'token' in renamed.columns:
        renamed['token_norm'] = renamed['token'].astype(str).map(norm_token)
    keep = list({
        'Dataset','Task','Subject','SentenceID','w_pos','token','token_norm','theta1','alpha1','beta1','gamma1'
    } & set(renamed.columns))
    return renamed[keep]

def load_eeg(base_dir: Path) -> pd.DataFrame:
    disc = discover(base_dir)
    frames: List[pd.DataFrame] = []
    for dataset, fd in disc.items():
        for path in fd.eeg_tabular:
            df = _read_table_auto(path)
            if df is None:
                continue
            mapped = _map_eeg_columns(df)
            if mapped is None:
                continue
            if 'Dataset' in mapped.columns:
                mapped['Dataset'] = mapped['Dataset'].fillna(dataset)
            else:
                mapped['Dataset'] = dataset
            # Try fill Task from folder name if missing
            if 'Task' not in mapped.columns or mapped['Task'].isna().all():
                task = detect_task_from_path(path) or np.nan
                mapped['Task'] = task
            frames.append(mapped)
    if not frames:
        heartbeat("INFO: No EEG tabular files mapped; EEG table will be empty.")
        return pd.DataFrame(columns=['Dataset','Task','Subject','SentenceID','w_pos','token','token_norm','theta1','alpha1','beta1','gamma1'])
    out = pd.concat(frames, ignore_index=True)
    # aggregate per canonical keys
    keys = ['Dataset','Task','Subject','SentenceID','w_pos','token_norm']
    val_cols = [c for c in ['theta1','alpha1','beta1','gamma1'] if c in out.columns]
    agg = out.groupby([k for k in keys if k in out.columns])[val_cols].mean().reset_index()
    return agg

# ----------------------- ET orchestrator -----------------------

def _process_subject_task(version_root: Path, et_path: Path) -> Optional[pd.DataFrame]:
    return _process_session_from_mat_path(version_root, et_path)

def load_et(base_dir: Path, n_jobs: int = -1) -> pd.DataFrame:
    disc = discover(base_dir)
    frames: List[pd.DataFrame] = []
    for dataset, fd in disc.items():
        version_root = base_dir / dataset
        if not fd.et_mat:
            continue
        if _HAS_JOBLIB and n_jobs != 1:
            results = Parallel(n_jobs=n_jobs)(delayed(_process_subject_task)(version_root, p) for p in fd.et_mat)
        else:
            results = [_process_subject_task(version_root, p) for p in fd.et_mat]
        dfs = [d for d in results if isinstance(d, pd.DataFrame)]
        if dfs:
            frames.append(pd.concat(dfs, ignore_index=True))
    if not frames:
        heartbeat("WARN: No ET data frames produced; ET table will be empty.")
        return pd.DataFrame(columns=['Dataset','Task','Subject','SentenceID','w_pos','token','token_norm','FFD','GD','TRT','GPT'])
    out = pd.concat(frames, ignore_index=True)
    # enforce types
    for c in ['SentenceID','w_pos']:
        if c in out.columns:
            out[c] = out[c].astype('Int64')
    return out

# ----------------------- merge -----------------------

def merge_et_eeg(et: pd.DataFrame, eeg: pd.DataFrame) -> pd.DataFrame:
    keys = ['Dataset','Task','Subject','SentenceID','w_pos','token_norm']
    # Left join ET with EEG
    merged = et.merge(eeg, on=[k for k in keys if k in et.columns and k in eeg.columns], how='left')
    # Append EEG-only rows
    if not eeg.empty:
        # Build anti-join keys present in EEG but not in ET
        have_all_keys_in_eeg = all(k in eeg.columns for k in keys)
        if have_all_keys_in_eeg:
            et_keys = et[keys].drop_duplicates() if not et.empty else pd.DataFrame(columns=keys)
            eeg_keys = eeg[keys].drop_duplicates()
            # anti-join: EEG keys not present in ET keys
            anti = eeg_keys.merge(et_keys, on=keys, how='left', indicator=True)
            eeg_only = anti.loc[anti['_merge'] == 'left_only', keys]
            if not eeg_only.empty:
                add = eeg_only.merge(eeg, on=keys, how='left')
                # ensure presence of columns expected downstream
                if 'token' not in add.columns:
                    add['token'] = np.nan
                for c in ['FFD','GD','TRT','GPT']:
                    if c not in add.columns:
                        add[c] = np.nan
                # align columns to merged
                add = add.reindex(columns=merged.columns, fill_value=np.nan)
                merged = pd.concat([merged, add], ignore_index=True)
    # order columns
    col_order = ['Dataset','Task','Subject','SentenceID','w_pos','token','token_norm','FFD','GD','TRT','GPT','theta1','alpha1','beta1','gamma1']
    for c in col_order:
        if c not in merged.columns:
            merged[c] = np.nan
    merged = merged[col_order]
    return merged

# ----------------------- QA -----------------------

def qa_summary(df: pd.DataFrame, disc: Dict[str, FileDiscovery], errors: Optional[Dict[str, List[str]]] = None) -> Dict:
    files = {
        'v1_et_mat': len(disc.get('v1', FileDiscovery([],[])).et_mat),
        'v2_et_mat': len(disc.get('v2', FileDiscovery([],[])).et_mat),
        'v1_eeg_tabular': len(disc.get('v1', FileDiscovery([],[])).eeg_tabular),
        'v2_eeg_tabular': len(disc.get('v2', FileDiscovery([],[])).eeg_tabular),
    }
    out = {
        'rows': int(len(df)),
        'subjects': int(df['Subject'].nunique()) if 'Subject' in df.columns else 0,
        'by_dataset': df.groupby('Dataset').size().to_dict() if 'Dataset' in df.columns and not df.empty else {},
        'by_task': df.groupby('Task').size().to_dict() if 'Task' in df.columns and not df.empty else {},
        'et_coverage_pct': {c: f"{df[c].notna().mean()*100:.1f}%" for c in ['FFD','GD','TRT','GPT'] if c in df.columns},
        'eeg_coverage_pct': {c: f"{df[c].notna().mean()*100:.1f}%" for c in ['theta1','alpha1','beta1','gamma1'] if c in df.columns},
        'files': files,
        'errors': errors or {}
    }
    return out

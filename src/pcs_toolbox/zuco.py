from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np, pandas as pd
from scipy.io import loadmat
from .common import token_norm, setup_logger, DATA_RAW, DATA_PROC, REPORTS, write_json, ensure_dir

LOG = setup_logger("pcs")

# Canonical column map
COLMAP = {
    # tokens/pos
    "Word":"token","word":"token","token":"token",
    "WordLineNumber":"w_pos","w_pos":"w_pos","Index":"w_pos","word_index":"w_pos","WordPosition":"w_pos","wordpos":"w_pos",
    # ET
    "FirstFixationDuration":"FFD","first_fix_dur":"FFD","FFD":"FFD",
    "GazeDuration":"GD","gaze_dur":"GD","gaze_duration":"GD","GD":"GD",
    "TotalReadingTime":"TRT","total_reading_time":"TRT","TRT":"TRT",
    "GoPastTime":"GPT","go_past_time":"GPT","gopasttime":"GPT","GPT":"GPT",
    # IDs
    "sentence_id":"SentenceID","SentenceID":"SentenceID","sentenceID":"SentenceID","sent_id":"SentenceID",
    "subject":"Subject","Subject":"Subject","participant":"Subject","subject_id":"Subject","subj":"Subject",
}

EEG_BANDS = ["theta1","alpha1","beta1","gamma1"]
ET_COLS   = ["FFD","GD","TRT","GPT"]
META_COLS = ["Dataset","Task","Subject","SentenceID","w_pos","token","token_norm"]

def _detect_task_from_path(p: Path) -> str:
    s = str(p).lower()
    if "task2" in s or "tsr" in s: return "TSR"
    if "task1" in s or "sr"  in s: return "SR"
    return "NR"

_EEG_SYNONYMS = {
    "theta":"theta1","theta1":"theta1","thetapower":"theta1","powertheta":"theta1","theta_1":"theta1","theta-1":"theta1",
    "alpha":"alpha1","alpha1":"alpha1","alphapower":"alpha1","poweralpha":"alpha1","alpha_1":"alpha1","alpha-1":"alpha1",
    "beta":"beta1","beta1":"beta1","betapower":"beta1","powerbeta":"beta1","beta_1":"beta1","beta-1":"beta1",
    "gamma":"gamma1","gamma1":"gamma1","gammapower":"gamma1","powergamma":"gamma1","gamma_1":"gamma1","gamma-1":"gamma1",
}

def _canon_name(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())

def _rename_cols(df: pd.DataFrame) -> pd.DataFrame:
    # First pass: canonical mappings by raw column name
    ren = {c: COLMAP[c] for c in df.columns if c in COLMAP}
    # Second pass: normalized name mapping (handles case/punct variants)
    norm_map = {c: _canon_name(c) for c in df.columns}
    # IDs and ET columns via normalized keys
    for c, cn in norm_map.items():
        if c in ren:
            continue
        if cn in ("word", "token"):
            ren[c] = "token"
        elif cn in ("wordlinenumber","index","wordindex","wordposition","wordpos"):
            ren[c] = "w_pos"
        elif cn in ("firstfixationduration","firstfixdur","ffd"):
            ren[c] = "FFD"
        elif cn in ("gazeduration","gazedur","gd"):
            ren[c] = "GD"
        elif cn in ("totalreadingtime","trt"):
            ren[c] = "TRT"
        elif cn in ("gopasttime","goptime","gpt"):
            ren[c] = "GPT"
        elif cn in ("sentenceid","sentid"):
            ren[c] = "SentenceID"
        elif cn in ("subject","subjectid","participant","subj"):
            ren[c] = "Subject"
    # EEG bands via normalized synonyms
    for c, cn in norm_map.items():
        if c in ren:
            continue
        if cn in _EEG_SYNONYMS:
            ren[c] = _EEG_SYNONYMS[cn]
    return df.rename(columns=ren)

def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["w_pos", *ET_COLS]: 
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def _read_table(path: Path) -> Optional[pd.DataFrame]:
    ext = path.suffix.lower()
    if ext in [".csv",".tsv",".txt"]:
        sep = "\t" if ext==".tsv" else ","
        return pd.read_csv(path, sep=sep)
    if ext==".mat":
        # Best-effort parse of common ZuCo ET .mat structures
        def _as_list(x):
            import numpy as _np
            if isinstance(x, (list, tuple)):
                return list(x)
            a = _np.asarray(x)
            if a.dtype == object:
                out = []
                for e in a.ravel():
                    try:
                        out.append(e.item() if hasattr(e, 'item') else e)
                    except Exception:
                        out.append(e)
                return out
            return a.ravel().tolist()
        try:
            mat = loadmat(path, squeeze_me=True, struct_as_record=False)
            keys = [k for k in mat.keys() if not k.startswith("__")]
            # Candidate direct arrays (flattened per-token)
            candidates = {
                'Word': None, 'token': None, 'Index': None, 'WordLineNumber': None,
                'FirstFixationDuration': None, 'GazeDuration': None,
                'TotalReadingTime': None, 'GoPastTime': None,
                'SentenceID': None, 'Subject': None
            }
            for k in keys:
                if k in candidates:
                    candidates[k] = _as_list(mat[k])
            # If at least two ET metrics present with aligned lengths, build table
            et_arrays = [candidates.get('FirstFixationDuration'), candidates.get('GazeDuration'), candidates.get('TotalReadingTime')]
            lens = [len(x) for x in et_arrays if isinstance(x, list)]
            if lens and len(set(lens)) == 1:
                n = lens[0]
                data = {
                    'token': candidates.get('Word') or candidates.get('token'),
                    'w_pos': candidates.get('WordLineNumber') or candidates.get('Index'),
                    'FFD': candidates.get('FirstFixationDuration'),
                    'GD': candidates.get('GazeDuration'),
                    'TRT': candidates.get('TotalReadingTime'),
                    'GPT': candidates.get('GoPastTime'),
                    'SentenceID': candidates.get('SentenceID'),
                    'Subject': candidates.get('Subject'),
                }
                # Trim or pad lists to length n
                for k, v in list(data.items()):
                    if v is None:
                        continue
                    if isinstance(v, list):
                        if len(v) > n:
                            data[k] = v[:n]
                        elif len(v) < n:
                            data[k] = v + [None] * (n - len(v))
                df = pd.DataFrame(data)
                # Normalize columns
                df = _rename_cols(df)
                return df
        except Exception:
            pass
        # Fallback: attempt to parse ET metrics from common ZuCo structs
        try:
            df2 = _read_et_from_mat_structs(path)
            if df2 is not None and not df2.empty:
                return df2
        except Exception:
            pass
        return None
    return None

def _guess_subject_from_path(path: Path) -> Optional[str]:
    name = path.stem
    # Examples: resultsZPH_SR, ZPH_SNR_corrected_ET, X01_task2_corrected_ET
    # Heuristics: letters between 'results' and first '_' OR prefix before first '_'
    import re
    m = re.match(r"results([A-Za-z]+)[_-]", name)
    if m:
        return m.group(1)
    m = re.match(r"([A-Za-z]{2,4})[_-]", name)
    if m:
        return m.group(1)
    return None

def _read_et_from_mat_structs(path: Path) -> Optional[pd.DataFrame]:
    """Best-effort extraction of ET metrics from ZuCo-like .mat structs.
    Looks for 'eyeevent.fixations', 'wordbounds', 'textbounds'.
    Returns per-token rows with approximate FFD, GD, TRT (GPT left NaN).
    """
    try:
        mat = loadmat(path, squeeze_me=True, struct_as_record=False)
    except Exception:
        return None
    eyedata = mat.get('eyeevent') or mat.get('eyeEvent') or mat.get('eye_event')
    wb = mat.get('wordbounds') or mat.get('wordBounds')
    tb = mat.get('textbounds') or mat.get('textBounds')
    if eyedata is None or wb is None or tb is None:
        return None
    # Fixations array: columns ~ [start_time, ?, duration]
    fix = None
    if hasattr(eyedata, 'fixations'):
        fx = eyedata.fixations
        fix = getattr(fx, 'data', fx)
    else:
        fix = getattr(eyedata, 'data', None)
    try:
        import numpy as _np
        f = _np.asarray(fix)
        if f.ndim == 1:
            f = f.reshape(-1, 3)
    except Exception:
        return None
    if f.size == 0:
        return None
    subj = _guess_subject_from_path(path)
    version = path.parents[2].name if len(path.parents) >= 2 else None
    # Estimate times per word using textbounds as sentence window, split evenly by word count
    rows: List[dict] = []
    min_latency = float(_np.nanmin(f[:, 0])) if f.size else 0.0
    global_w = 0
    def _safe_len(x) -> int:
        try:
            return len(x)
        except Exception:
            try:
                return int(x)
            except Exception:
                return 0
    try:
        n_sent = _safe_len(wb)
    except Exception:
        n_sent = 0
    for sent_idx in range(n_sent):
        try:
            sent_bounds = tb[sent_idx]
            sent_start = float(sent_bounds[0])
            sent_end = float(sent_bounds[1])
        except Exception:
            continue
        try:
            sent_wb = wb[sent_idx]
            n_words = _safe_len(getattr(sent_wb, 'content', sent_wb))
        except Exception:
            n_words = 0
        if n_words <= 0:
            continue
        dur = 0.0
        try:
            ds = sent_end - sent_start
            dur = float(ds) / max(1, int(n_words)) if ds and ds > 0 else 0.0
        except Exception:
            dur = 0.0
        for w_pos in range(n_words):
            start_t = sent_start + (w_pos * dur) + min_latency
            end_t = start_t + dur
            mask = (f[:, 0] >= start_t) & (f[:, 0] < end_t)
            fseg = f[mask]
            ffd = float(fseg[0, 2]) if len(fseg) > 0 else _np.nan
            trt = float(_np.nansum(fseg[:, 2])) if len(fseg) > 0 else _np.nan
            gd = float(_np.nansum(fseg[:-1, 2])) if len(fseg) > 1 else (ffd if not _np.isnan(ffd) else _np.nan)
            rows.append({
                'Dataset': version,
                'Subject': subj,
                'SentenceID': int(sent_idx+1),
                'w_pos': int(w_pos+1),
                'FFD': ffd, 'GD': gd, 'TRT': trt, 'GPT': _np.nan,
            })
            global_w += 1
    if not rows:
        return None
    df = pd.DataFrame(rows)
    return df

def _aggregate_eeg(df_eeg: pd.DataFrame) -> pd.DataFrame:
    """Group by per-token keys and average bands."""
    if df_eeg.empty: return df_eeg
    meta_present = [c for c in META_COLS if c in df_eeg.columns]
    band_present = [c for c in EEG_BANDS if c in df_eeg.columns]
    use = meta_present + band_present
    g = (df_eeg[use]
         .groupby(["Dataset","Task","Subject","SentenceID","w_pos","token_norm"], dropna=False)
         .mean(numeric_only=True)
         .reset_index())
    return g

def _is_et(df: pd.DataFrame) -> bool:
    return len(set(df.columns) & set(ET_COLS)) >= 2

def _is_eeg(df: pd.DataFrame) -> bool:
    return len(set(df.columns) & set(EEG_BANDS)) >= 1

def load_all(write_outputs: bool=True) -> tuple[pd.DataFrame, dict]:
    qa = {"files": [], "errors": [], "counts":{"et_rows":0,"eeg_rows":0}}
    et_rows, eeg_rows = [], []
    for dataset in ["v1","v2"]:
        for path in (DATA_RAW/dataset).rglob("*.*"):
            if path.suffix.lower() not in {".csv",".tsv",".txt",".mat"}: 
                continue
            task = _detect_task_from_path(path)
            df = _read_table(path)
            if df is None or df.empty:
                qa["errors"].append({"file":str(path),"error":"unreadable or empty"})
                continue
            df = _rename_cols(df)
            if "token" in df.columns:
                df["token_norm"] = df["token"].astype(str).map(token_norm)
            if "Subject" not in df.columns:
                df["Subject"] = _guess_subject_from_path(path)
            if "SentenceID" not in df.columns: df["SentenceID"] = None
            if "w_pos" not in df.columns: df["w_pos"] = None
            df["Dataset"], df["Task"] = dataset, task
            df = _coerce_numeric(df)
            keep = [c for c in (META_COLS + ET_COLS + EEG_BANDS) if c in df.columns]
            df = df[keep].copy()
            meta = {"file":str(path), "dataset":dataset, "task":task,
                    "cols":list(df.columns), "n":int(df.shape[0]),
                    "is_et":_is_et(df), "is_eeg":_is_eeg(df)}
            qa["files"].append(meta)
            if meta["is_et"]:
                et_rows.append(df[[c for c in df.columns if c not in EEG_BANDS]])
                qa["counts"]["et_rows"] += int(df.shape[0])
            if meta["is_eeg"]:
                eeg_rows.append(df[[c for c in df.columns if c not in ET_COLS]])
                qa["counts"]["eeg_rows"] += int(df.shape[0])

    et  = pd.concat(et_rows,  ignore_index=True) if et_rows  else pd.DataFrame(columns=META_COLS+ET_COLS)
    eeg = pd.concat(eeg_rows, ignore_index=True) if eeg_rows else pd.DataFrame(columns=META_COLS+EEG_BANDS)

    eeg_agg = _aggregate_eeg(eeg) if not eeg.empty else eeg

    keys = ["Dataset","Task","Subject","SentenceID","w_pos","token_norm"]
    if et.empty:
        merged = eeg_agg.copy()
    else:
        merged = pd.merge(et, eeg_agg, on=keys, how="outer", suffixes=("","_eeg"))
        if "token" in merged.columns and "token_eeg" in merged.columns:
            merged["token"] = merged["token"].fillna(merged["token_eeg"])
            merged = merged.drop(columns=[c for c in merged.columns if c.endswith("_eeg")])

    order = META_COLS + ET_COLS + EEG_BANDS
    merged = merged[[c for c in order if c in merged.columns]].copy()
    merged = merged.dropna(subset=["token_norm"]).reset_index(drop=True)

    # QA sanity: per-sentence eeg coverage vs skips
    anomalies: List[dict] = []
    if not merged.empty and all(k in merged.columns for k in ["Dataset","Task","Subject","SentenceID"]):
        def _is_fixated(row) -> bool:
            vals = [row[c] for c in ET_COLS if c in merged.columns]
            vals = [v for v in vals if pd.notna(v)]
            return any((isinstance(v,(int,float)) and v > 0) for v in vals)
        merged["_fixated"] = merged.apply(_is_fixated, axis=1)
        has_eeg = merged[[c for c in EEG_BANDS if c in merged.columns]].notna().any(axis=1)
        merged["_has_eeg"] = has_eeg
        # group by sentence
        grp_keys = ["Dataset","Task","Subject","SentenceID"]
        for keys, grp in merged.groupby(grp_keys, dropna=False):
            n_tokens = int(grp.shape[0])
            n_eeg = int(grp["_has_eeg"].sum())
            n_skips = int((~grp["_fixated"]).sum())
            if (n_eeg + n_skips) != n_tokens:
                anomalies.append({"keys": tuple(keys), "n_tokens": n_tokens, "n_eeg": n_eeg, "n_skips": n_skips})

    summary = {
        "rows_et": int(et.shape[0]), "rows_eeg": int(eeg.shape[0]),
        "rows_merged": int(merged.shape[0]),
        "n_subjects": int(merged["Subject"].nunique(dropna=True)) if "Subject" in merged else 0,
        "n_sentences": int(merged["SentenceID"].nunique(dropna=True)) if "SentenceID" in merged else 0,
        "n_tokens": int(merged["token_norm"].nunique(dropna=True)),
        "datasets": merged["Dataset"].value_counts(dropna=True).to_dict() if "Dataset" in merged else {},
        "tasks": merged["Task"].value_counts(dropna=True).to_dict() if "Task" in merged else {},
        "n_anomalies": len(anomalies),
    }
    qa["summary"] = summary
    if anomalies:
        qa["anomalies"] = anomalies

    if write_outputs:
        ensure_dir(DATA_PROC)
        ensure_dir(REPORTS)
        out_csv = DATA_PROC/"zuco_aligned.csv"
        merged.drop(columns=[c for c in ["_fixated","_has_eeg"] if c in merged.columns], inplace=True, errors="ignore")
        merged.to_csv(out_csv, index=False)
        write_json(REPORTS/"zuco_loader_qa.json", qa)
        LOG.info(f"Wrote {out_csv} and reports/zuco_loader_qa.json")

    return merged, qa

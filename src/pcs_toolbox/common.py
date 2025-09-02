from __future__ import annotations
import re, unicodedata, logging, os, json
from pathlib import Path

def setup_logger(name: str = "pcs"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger

def token_norm(s: str) -> str:
    if s is None: return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def write_json(path: str | Path, obj: dict):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def ensure_dir(path: str | Path):
    Path(path).mkdir(parents=True, exist_ok=True)

DATA_RAW = Path("data/raw_public/zuco")
DATA_PROC = Path("data/processed")
REPORTS  = Path("reports")


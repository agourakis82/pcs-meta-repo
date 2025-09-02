from __future__ import annotations
from pathlib import Path
import json

def summarize_mat(path: Path) -> dict:
    try:
        from scipy.io import loadmat
        mat = loadmat(path, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        return {"file": str(path), "error": str(e)}
    keys = [k for k in mat.keys() if not k.startswith("__")]
    info = {"file": str(path), "keys": []}
    for k in keys:
        v = mat.get(k)
        tname = type(v).__name__
        shape = getattr(v, 'shape', None)
        try:
            shape = tuple(shape) if shape is not None else None
        except Exception:
            shape = None
        info["keys"].append({"name": k, "type": tname, "shape": shape})
    return info

def main() -> int:
    base = Path('data/raw_public/zuco')
    out = []
    for p in base.rglob('*.mat'):
        out.append(summarize_mat(p))
    Path('reports').mkdir(parents=True, exist_ok=True)
    (Path('reports') / 'zuco_mat_keys.json').write_text(json.dumps(out, indent=2))
    print('[inspect_mat] Wrote reports/zuco_mat_keys.json with', len(out), 'files')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())


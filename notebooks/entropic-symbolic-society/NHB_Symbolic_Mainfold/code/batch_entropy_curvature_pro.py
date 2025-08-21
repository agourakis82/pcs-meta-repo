#!/usr/bin/env python3
# batch_entropy_curvature_pro.py
# Executa compute_entropy_curvature_pro.py a partir de um YAML.

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    print("PyYAML requerido: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HERE = Path(__file__).parent.resolve()
PY = HERE / "compute_entropy_curvature_pro.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-all", default="entropy_curvature_all.csv")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    outs = []
    for job in cfg.get("jobs", []):
        graph = job["graph"]
        regime = job.get("regime", "")
        betas = " ".join(map(str, job.get("beta", [1.0])))
        out = job.get("out", "entropy_curvature.csv")
        no_curv = job.get("no_curvature", False)
        curv_undirected = job.get("curv_undirected", True)
        curv_sample = str(job.get("curv_sample", 2000))
        ricci_method = job.get("ricci_method", "OTD")
        seed = str(job.get("seed", 42))

        cmd = (
            [sys.executable, str(PY), "--graph", graph, "--beta"]
            + betas.split()
            + [
                "--out",
                out,
                "--regime",
                regime,
                "--ricci-method",
                ricci_method,
                "--curv-sample",
                curv_sample,
                "--seed",
                seed,
            ]
        )
        if curv_undirected:
            cmd.insert(len(cmd) - 2, "--curv-undirected")
        if no_curv:
            cmd.insert(len(cmd) - 2, "--no-curvature")

        print(">>", " ".join(shlex.quote(c) for c in cmd))
        subprocess.run(cmd, check=True)
        outs.append(out)

    # concatena em out-all
    if outs:
        with open(args.out_all, "w") as w:
            with open(outs[0]) as f:
                w.write(f.readline())  # header
            for fpath in outs:
                with open(fpath) as f:
                    _ = f.readline()
                    for line in f:
                        w.write(line)
        print("Wrote", args.out_all)


if __name__ == "__main__":
    main()

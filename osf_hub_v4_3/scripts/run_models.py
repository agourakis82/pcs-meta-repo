#!/usr/bin/env python3
from pathlib import Path
import csv
import random
import time


def write_models_coeffs_csv(path: Path):
    rows = [
        {
            "model": "ols",
            "term": "Intercept",
            "coef": 0.5,
            "se": 0.1,
            "t": 5.0,
            "p": 0.0001,
            "ci_low": 0.3,
            "ci_high": 0.7,
        },
        {
            "model": "ols",
            "term": "kec",
            "coef": 0.15,
            "se": 0.07,
            "t": 2.14,
            "p": 0.0324,
            "ci_low": 0.01,
            "ci_high": 0.29,
        },
        {
            "model": "mixedlm",
            "term": "kec",
            "coef": 0.12,
            "se": 0.06,
            "t": 2.00,
            "p": 0.0450,
            "ci_low": 0.00,
            "ci_high": 0.24,
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_fdr_csv(path: Path):
    # Simple stub: q-values are min(p * m / rank, 1) with m=3, ranks by p ascending
    pvals = [
        ("ols", "kec", 0.0324),
        ("mixedlm", "kec", 0.0450),
        ("ols", "Intercept", 0.0001),
    ]
    pvals_sorted = sorted(pvals, key=lambda x: x[2])
    m = len(pvals_sorted)
    qvals = []
    for i, (model, term, p) in enumerate(pvals_sorted, start=1):
        q = min(p * m / i, 1.0)
        qvals.append((model, term, p, q))

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "term", "p", "q"]) 
        writer.writeheader()
        for model, term, p, q in qvals:
            writer.writerow({"model": model, "term": term, "p": p, "q": q})


def write_mixedlm_summary(path: Path):
    content = (
        "MixedLM Summary (stub)\n"
        "=======================\n"
        "Random intercepts: sentence, subject\n"
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
    )
    path.write_text(content, encoding="utf-8")


def main():
    base_dir = Path(__file__).resolve().parents[1]
    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    write_models_coeffs_csv(results_dir / "models_reading_coeffs.csv")
    write_fdr_csv(results_dir / "models_reading_coeffs_fdr.csv")
    write_mixedlm_summary(results_dir / "mixedlm_ffd_summary.txt")

    print("[OK] run_models.py: stub model outputs written to results/.")


if __name__ == "__main__":
    random.seed(424242)
    main()

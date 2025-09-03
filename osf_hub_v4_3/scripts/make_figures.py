#!/usr/bin/env python3
from pathlib import Path
import base64


# 1x1 PNG (transparent) as a safe placeholder
PNG_1x1_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/akm6XkAAAAASUVORK5CYII="
)


def write_png(path: Path):
    data = base64.b64decode(PNG_1x1_B64)
    path.write_bytes(data)


def main():
    base_dir = Path(__file__).resolve().parents[1]
    fig_dir = base_dir / "results" / "figures" / "metrics"
    fig_dir.mkdir(parents=True, exist_ok=True)

    write_png(fig_dir / "F2_.png")
    write_png(fig_dir / "F3_.png")

    print(
        "[OK] make_figures.py: placeholder figures F2_/F3_ created in "
        "results/figures/metrics."
    )


if __name__ == "__main__":
    main()

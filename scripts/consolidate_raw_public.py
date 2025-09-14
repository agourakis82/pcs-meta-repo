#!/usr/bin/env python3
"""
Consolidate all raw-public datasets into canonical locations.

What it does
- Discovers candidate sources (repo and optional external FASTDATA) for each dataset
  defined in config/datasets.yaml.
- Verifies integrity by computing SHA-256 for each file.
- Plans/executes consolidation into the canonical raw_dir (link/copy).
- Emits a manifest (JSON) with actions, checksums, conflicts and stats.

Defaults
- Dry-run by default (no filesystem changes).
- Mode: symlink (saves space) or copy (safer portability).

Usage examples
  Dry-run (all datasets):
    python scripts/consolidate_raw_public.py --dry-run

  Apply with symlinks (recommended):
    python scripts/consolidate_raw_public.py --apply --mode link

  Only SWOW (include external FASTDATA hints from config/data_root.yaml):
    python scripts/consolidate_raw_public.py --dataset swow --include-external --apply

Notes
- This script does NOT download anything. It only discovers existing files
  across repo paths (data/raw_public, scripts/data/raw_public) and optional
  external roots defined in config/data_root.yaml (layout.*).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import yaml

# Local config resolver (repo-relative import)
import sys

# Ensure repo src/ is on sys.path when executed as a script
_HERE = Path(__file__).resolve().parent
_SRC = (_HERE.parent / "src").resolve()
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.paths import PathsConfig


@dataclass
class FileEntry:
    src_root: str
    src_path: str
    rel_path: str
    sha256: str
    bytes: int


@dataclass
class PlannedAction:
    dataset: str
    action: str  # link|copy|skip|conflict
    reason: str
    src: str
    dst: str
    sha256: str
    bytes: int


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dataset_config(repo_root: Path) -> dict:
    cfg_path = repo_root / "config" / "datasets.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def iter_expected_patterns(dataset_name: str, config: dict) -> List[str]:
    # SWOW is special (top-level section)
    if dataset_name == "swow":
        section = config.get("swow", {})
        return section.get("expected_files", ["**/*"])

    # RT and EEG sections
    for group in ("datasets_rt", "datasets_eeg"):
        section = config.get(group, {})
        if dataset_name in section:
            return section[dataset_name].get("expected_files", ["**/*"])

    return ["**/*"]


def get_raw_dir(dataset_name: str, config: dict) -> str:
    if dataset_name == "swow":
        return config.get("swow", {}).get("raw_dir", "data/raw_public/swow")
    for group in ("datasets_rt", "datasets_eeg"):
        if dataset_name in config.get(group, {}):
            return config[group][dataset_name].get("raw_dir")
    raise ValueError(f"Dataset not found in configuration: {dataset_name}")


def dataset_keys(config: dict) -> List[str]:
    keys: List[str] = ["swow"]
    for group in ("datasets_rt", "datasets_eeg"):
        keys.extend(sorted(config.get(group, {}).keys()))
    # Deduplicate while preserving order
    seen: Set[str] = set()
    out: List[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def short_from_raw_dir(raw_dir: str) -> str:
    # data/raw_public/<short>
    parts = Path(raw_dir).parts
    try:
        idx = parts.index("raw_public")
        return parts[idx + 1]
    except Exception:
        # fallback to last component
        return Path(raw_dir).name


def discover_source_roots(
    repo_root: Path,
    ds_name: str,
    raw_dir: str,
    include_external: bool,
    paths_cfg: PathsConfig,
    full_config: dict,
) -> List[Path]:
    """Return a prioritized list of candidate source roots for the dataset."""
    roots: List[Path] = []

    # 1) Repo canonical target (may already contain files)
    target = repo_root / raw_dir
    roots.append(target)

    # 2) scripts/ mirror of raw_public
    scripts_mirror = repo_root / "scripts" / raw_dir
    if scripts_mirror.exists():
        roots.append(scripts_mirror)

    # 3) Dataset-specific additional locations
    short = short_from_raw_dir(raw_dir)

    # SWOW: languages under swow/<lang>
    if ds_name == "swow":
        for base in (repo_root / "data" / "raw_public" / "swow", repo_root / "scripts" / "data" / "raw_public" / "swow"):
            if base.exists():
                roots.append(base)

    # ZuCo: common OSF layouts under scripts/data/raw_public/zuco and external
    if short == "zuco":
        candidates = [
            repo_root / "scripts" / "data" / "raw_public" / "zuco",
            repo_root / "scripts" / "data" / "raw_public" / "zuco" / "v1" / "osfstorage",
            repo_root / "scripts" / "data" / "raw_public" / "zuco" / "v2" / "osfstorage",
        ]
        for c in candidates:
            if c.exists():
                roots.append(c)

    # Other datasets under scripts/data/raw_public/<short>
    generic = repo_root / "scripts" / "data" / "raw_public" / short
    if generic.exists():
        roots.append(generic)

    # 4) External (FASTDATA) if requested
    if include_external:
        dr = paths_cfg.data_root
        layout = dr.get("layout", {}) if isinstance(dr, dict) else {}
        # Known external keys
        ext_keys = [
            "raw_external",
            "raw_zuco_v1",
            "raw_zuco_v2",
        ]
        for k in ext_keys:
            p = layout.get(k)
            if isinstance(p, str):
                # Interpolate {data_root}
                root_str = p.format(data_root=dr.get("data_root", ""))
                xp = Path(root_str)
                if xp.exists():
                    # Use entire tree for discovery (will be filtered by expected patterns)
                    roots.append(xp)

    # Deduplicate while preserving order
    seen: Set[str] = set()
    uniq: List[Path] = []
    for r in roots:
        rs = str(r.resolve())
        if rs not in seen and r.exists():
            uniq.append(r)
            seen.add(rs)
    return uniq


def collect_files(
    roots: List[Path], patterns: Iterable[str],
) -> Tuple[List[FileEntry], Dict[str, List[FileEntry]]]:
    entries: List[FileEntry] = []
    by_hash: Dict[str, List[FileEntry]] = {}
    for root in roots:
        for pat in patterns:
            for f in root.rglob(pat):
                if not f.is_file():
                    continue
                # Skip common ignored files
                if f.name.startswith("."):
                    continue
                try:
                    digest = sha256_of(f)
                    rel = str(f.relative_to(root))
                    e = FileEntry(
                        src_root=str(root),
                        src_path=str(f),
                        rel_path=rel,
                        sha256=digest,
                        bytes=f.stat().st_size,
                    )
                    entries.append(e)
                    by_hash.setdefault(digest, []).append(e)
                except Exception:
                    # Best-effort: ignore unreadable files
                    continue
    return entries, by_hash


def plan_consolidation(
    dataset: str,
    target_root: Path,
    entries: List[FileEntry],
    by_hash: Dict[str, List[FileEntry]],
    existing_targets: Optional[Set[str]] = None,
) -> List[PlannedAction]:
    actions: List[PlannedAction] = []
    existing_targets = existing_targets or set()

    # Map existing files in target by hash to avoid duplicate work
    target_hashes: Set[str] = set()
    if target_root.exists():
        for f in target_root.rglob("*"):
            if f.is_file():
                try:
                    target_hashes.add(sha256_of(f))
                except Exception:
                    pass

    # For each unique hash choose one representative (prefer sources under scripts/ then external)
    def score_src(path: str) -> int:
        # Lower score = preferred
        p = path.lower()
        if "/scripts/" in p:
            return 0
        if "/data/raw_public/" in p:
            return 1
        return 2

    for h, group in by_hash.items():
        # Already present in target? skip
        if h in target_hashes:
            # Determine an arbitrary dst for reporting
            actions.append(
                PlannedAction(
                    dataset=dataset,
                    action="skip",
                    reason="already_present_by_hash",
                    src=group[0].src_path,
                    dst=str(target_root),
                    sha256=h,
                    bytes=group[0].bytes,
                )
            )
            continue

        # Choose best representative
        rep = sorted(group, key=lambda e: (score_src(e.src_path), len(e.rel_path)))[0]
        dst = target_root / rep.rel_path

        # If destination path already exists with different content, mark conflict (will suffix)
        final_dst = dst
        if final_dst.exists():
            try:
                if sha256_of(final_dst) != h:
                    # add short hash suffix to filename
                    p = Path(final_dst)
                    stem = p.stem
                    suff = p.suffix
                    final_dst = p.with_name(f"{stem}__{h[:8]}{suff}")
                    actions.append(
                        PlannedAction(
                            dataset=dataset,
                            action="conflict",
                            reason="same_path_different_hash",
                            src=rep.src_path,
                            dst=str(final_dst),
                            sha256=h,
                            bytes=rep.bytes,
                        )
                    )
            except Exception:
                pass

        actions.append(
            PlannedAction(
                dataset=dataset,
                action="stage",
                reason="unique_hash",
                src=rep.src_path,
                dst=str(final_dst),
                sha256=h,
                bytes=rep.bytes,
            )
        )

    return actions


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def do_apply(action: PlannedAction, mode: str) -> Tuple[str, str]:
    """Execute one planned action. Returns (result_action, message)."""
    if action.action not in {"stage", "conflict"}:
        return (action.action, "no-op")

    src = Path(action.src)
    dst = Path(action.dst)
    ensure_parent(dst)
    if mode == "link":
        if dst.exists():
            return ("skip", "dst_exists")
        os.link(src, dst) if hasattr(os, "link") else os.symlink(src, dst)
        return ("linked", "hardlink_or_symlink_created")
    elif mode == "copy":
        import shutil

        if dst.exists():
            return ("skip", "dst_exists")
        shutil.copy2(src, dst)
        return ("copied", "file_copied")
    else:
        return ("error", f"invalid mode: {mode}")


def main():
    parser = argparse.ArgumentParser(description="Consolidate raw-public datasets")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repo root")
    parser.add_argument("--dataset", action="append", help="Dataset(s) to process (default: all)")
    parser.add_argument("--include-external", action="store_true", help="Include FASTDATA/external roots from data_root.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Only plan; no changes (default)")
    parser.add_argument("--apply", action="store_true", help="Apply planned actions")
    parser.add_argument("--mode", choices=["link", "copy"], default="link", help="Consolidation mode (default: link)")
    parser.add_argument("--report", type=Path, default=Path("reports/provenance/raw_public_manifest.json"), help="Output manifest path")

    args = parser.parse_args()
    if not args.apply:
        args.dry_run = True

    repo_root = args.repo.resolve()
    cfg = load_dataset_config(repo_root)
    paths_cfg = PathsConfig()

    datasets = args.dataset if args.dataset else dataset_keys(cfg)

    manifest: Dict[str, dict] = {"datasets": {}, "summary": {}}
    total_stage = total_skip = total_conflicts = 0

    for ds in datasets:
        raw_dir = get_raw_dir(ds, cfg)
        patterns = iter_expected_patterns(ds, cfg)
        roots = discover_source_roots(repo_root, ds, raw_dir, args.include_external, paths_cfg, cfg)

        entries, by_hash = collect_files(roots, patterns)
        target_root = repo_root / raw_dir

        actions = plan_consolidation(ds, target_root, entries, by_hash)

        applied: List[dict] = []
        stats = {"planned": len(actions), "linked": 0, "copied": 0, "skipped": 0, "conflicts": 0}

        if not args.dry_run:
            for a in actions:
                res, msg = do_apply(a, args.mode)
                rec = asdict(a)
                rec["result"] = res
                rec["message"] = msg
                applied.append(rec)
                if res in ("linked", "copied"):
                    stats[res + ""] += 1
                elif res == "skip":
                    stats["skipped"] += 1
                elif res == "conflict":
                    stats["conflicts"] += 1
        else:
            # Dry-run: just record planned
            for a in actions:
                rec = asdict(a)
                rec["result"] = "planned"
                rec["message"] = "dry_run"
                applied.append(rec)

        manifest["datasets"][ds] = {
            "raw_dir": raw_dir,
            "patterns": patterns,
            "source_roots": [str(r) for r in roots],
            "files_seen": len(entries),
            "unique_hashes": len(by_hash),
            "actions": applied,
            "stats": stats,
        }

        total_stage += stats.get("planned", 0)
        total_skip += stats.get("skipped", 0)
        total_conflicts += stats.get("conflicts", 0)

    manifest["summary"] = {
        "datasets": datasets,
        "total_planned": total_stage,
        "total_skipped": total_skip,
        "total_conflicts": total_conflicts,
        "mode": args.mode,
        "dry_run": bool(args.dry_run),
    }

    # Ensure report dir exists
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest written: {args.report}")
    print(json.dumps(manifest["summary"], indent=2))


if __name__ == "__main__":
    main()

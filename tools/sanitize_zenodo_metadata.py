#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# ORCID format accepted by Zenodo deposit (identifier only, no URL)
ORCID_NUM_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_orcid(value: str) -> Tuple[str | None, str | None]:
    """
    Normalize an ORCID value to numeric-only format.
    - Strip https://orcid.org/ prefix if present
    - If starts with 0009- or does not match ORCID_NUM_RE, return (None, reason)
    - Otherwise return (normalized, None)
    """
    original = value.strip()
    v = original
    if v.lower().startswith("http://orcid.org/"):
        v = v[len("http://orcid.org/"):]
    if v.lower().startswith("https://orcid.org/"):
        v = v[len("https://orcid.org/"):]
    # Drop URL params/fragments if any
    v = v.split("?")[0].split("#")[0]
    if v.startswith("0009-"):
        return None, "unsupported_orcid_prefix_0009"
    if not ORCID_NUM_RE.match(v):
        return None, "invalid_orcid_format"
    return v, None


def sanitize_creators(creators: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Sanitize creators list for Zenodo deposit schema (name/orcid/affiliation)."""
    changes: List[Dict[str, Any]] = []
    out: List[Dict[str, Any]] = []
    for idx, c in enumerate(creators):
        name = c.get("name") or c.get("full_name")
        aff = c.get("affiliation")
        orcid = c.get("orcid")
        rec_change: Dict[str, Any] = {"index": idx}
        if isinstance(orcid, str) and orcid.strip():
            norm, reason = normalize_orcid(orcid)
            if norm:
                if norm != orcid:
                    rec_change["orcid_normalized_from"] = orcid
                    rec_change["orcid_normalized_to"] = norm
                orcid_out = norm
            else:
                # drop invalid
                rec_change["orcid_removed"] = orcid
                rec_change["reason"] = reason
                orcid_out = None
        else:
            orcid_out = None
        # Keep the provided name as-is (assume "Surname, Given" already)
        out_entry: Dict[str, Any] = {"name": name} if name else {}
        if aff:
            out_entry["affiliation"] = aff
        if orcid_out:
            out_entry["orcid"] = orcid_out
        # Only record change if any noted
        if any(k for k in rec_change.keys() if k != "index"):
            changes.append(rec_change)
        out.append(out_entry)
    return out, changes


def sanitize_zenodo(input_path: Path, output_path: Path) -> Dict[str, Any]:
    data = load_json(input_path)
    log: Dict[str, Any] = {"input": str(input_path), "output": str(output_path)}
    # Ensure required high-level fields are preserved
    data.setdefault("upload_type", "software")
    # Sanitize creators
    creators = data.get("creators") or []
    if not isinstance(creators, list):
        creators = []
    creators_sane, creators_changes = sanitize_creators(creators)
    data["creators"] = creators_sane
    log["creators_changes"] = creators_changes
    # No change to related_identifiers here; we validate downstream
    save_json(output_path, data)
    return log


def sanitize_citation(citation_in: Path, citation_out: Path) -> Dict[str, Any]:
    """
    Produce a sanitized copy of CITATION.cff for release artifact:
    - Convert `orcid:` URL to numeric-only when valid
    - Remove `orcid:` when invalid or 0009-
    """
    out_log: Dict[str, Any] = {"input": str(citation_in), "output": str(citation_out), "orcid_actions": []}
    if not citation_in.exists():
        return out_log
    txt = citation_in.read_text(encoding="utf-8")

    def repl(match: re.Match) -> str:
        full = match.group(0)
        url = match.group(1)
        norm, reason = normalize_orcid(url)
        if norm:
            out_log["orcid_actions"].append({"from": url, "to": norm})
            return f"orcid: \"{norm}\""
        else:
            out_log["orcid_actions"].append({"from": url, "removed": True, "reason": reason})
            # Remove the line entirely
            return ""

    # Replace lines like: orcid: "https://orcid.org/0000-..." or orcid: "0000-..."
    txt2 = re.sub(r"(?m)^\s*orcid:\s*\"([^\"]+)\"\s*$", repl, txt)
    citation_out.write_text(txt2, encoding="utf-8")
    return out_log


def main() -> int:
    ap = argparse.ArgumentParser(description="Sanitize Zenodo metadata for release (ORCID, creators)")
    ap.add_argument("--input", default=str(ROOT / ".zenodo.json"), help="Path to .zenodo.json")
    ap.add_argument("--output", default=str(ROOT / ".zenodo.release.json"), help="Path to write sanitized JSON")
    ap.add_argument("--citation", default=str(ROOT / "CITATION.cff"), help="Path to CITATION.cff")
    ap.add_argument("--citation-output", default=str(ROOT / "CITATION.release.cff"), help="Path to write sanitized CITATION copy")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    cit_in = Path(args.citation)
    cit_out = Path(args.citation_output)

    log: Dict[str, Any] = {"actions": []}
    log["zenodo"] = sanitize_zenodo(input_path, output_path)
    log["citation"] = sanitize_citation(cit_in, cit_out)
    save_json(REPORTS / "zenodo_sanitize_log.json", log)
    print("sanitize: OK — reports/zenodo_sanitize_log.json, .zenodo.release.json, CITATION.release.cff")
    return 0


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

ORCID_NUM_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ALLOWED_LICENSES = {"cc-by-4.0", "CC-BY-4.0", "CC BY 4.0"}
ALLOWED_REL = {
    "isNewVersionOf",
    "isPreviousVersionOf",
    "isVersionOf",
    "isPartOf",
    "isSupplementTo",
    "isReferencedBy",
    "isSupplementedBy",
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    input_path = ROOT / ".zenodo.release.json"
    errors: List[str] = []
    warnings: List[str] = []
    if not input_path.exists():
        errors.append(f"Missing {input_path}")
        result = {"valid": False, "errors": errors, "warnings": warnings}
        (REPORTS / "zenodo_validate.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("validate: errors — see reports/zenodo_validate.json", file=sys.stderr)
        return 1

    data = load_json(input_path)

    # upload_type
    ut = data.get("upload_type")
    if ut != "software":
        errors.append("upload_type must be 'software'")

    # creators
    creators = data.get("creators") or []
    if not isinstance(creators, list) or not creators:
        errors.append("creators must be a non-empty list")
    else:
        for i, c in enumerate(creators):
            name = c.get("name")
            if not name:
                errors.append(f"creators[{i}].name is required")
            orcid = c.get("orcid")
            if orcid:
                if orcid.startswith("0009-"):
                    errors.append(f"creators[{i}].orcid starts with 0009- (not accepted by Zenodo)")
                if not ORCID_NUM_RE.match(orcid):
                    errors.append(f"creators[{i}].orcid not valid numeric ORCID: {orcid}")

    # license
    lic = data.get("license")
    if lic and lic not in ALLOWED_LICENSES:
        warnings.append(f"license '{lic}' not in canonical spellings; prefer 'cc-by-4.0'")
    elif not lic:
        warnings.append("license not set; prefer 'cc-by-4.0'")

    # version
    if not data.get("version"):
        errors.append("version is required")

    # related_identifiers
    rels = data.get("related_identifiers") or []
    if rels and isinstance(rels, list):
        for j, r in enumerate(rels):
            rid = r.get("identifier")
            rel = r.get("relation")
            scheme = r.get("scheme")
            if not rid or not rel:
                errors.append(f"related_identifiers[{j}] missing identifier/relation")
            else:
                if rel not in ALLOWED_REL:
                    warnings.append(f"related_identifiers[{j}].relation '{rel}' is uncommon")
            if scheme and scheme not in ("doi", "url"):
                warnings.append(f"related_identifiers[{j}].scheme '{scheme}' not expected")

    result = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    (REPORTS / "zenodo_validate.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if errors:
        print("validate: errors — see reports/zenodo_validate.json", file=sys.stderr)
        return 1
    print("validate: OK — reports/zenodo_validate.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())


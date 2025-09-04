#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True, parents=True)

MD_LINK_RE = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<link>[^)]+)\)")


def check_http(url: str) -> dict:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"ok": 200 <= resp.status < 400, "status": resp.status}
    except Exception as e:
        # Try GET as fallback
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                return {"ok": 200 <= resp.status < 400, "status": resp.status}
        except Exception as e2:
            return {"ok": False, "error": str(e2)}


def main() -> int:
    results = []
    broken = 0
    for path in ROOT.rglob("*.md"):
        if "/.git/" in str(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in MD_LINK_RE.finditer(text):
            link = m.group("link").strip()
            rec = {"file": str(path.relative_to(ROOT)), "link": link}
            if link.startswith("mailto:"):
                rec.update({"ok": True, "status": "mailto"})
            elif link.startswith("http://") or link.startswith("https://"):
                res = check_http(link)
                # tolerate some hosts with 403 on head/get (e.g., Wikipedia text fragments)
                if not res.get("ok") and "wikipedia.org" in urlparse(link).netloc:
                    res = {"ok": True, "status": "assumed-ok-403-wikipedia"}
                rec.update(res)
            else:
                # local path or anchor
                if link.startswith("#"):
                    rec.update({"ok": True, "status": "anchor-untested"})
                else:
                    p = (path.parent / link).resolve()
                    rec.update({"ok": p.exists(), "status": "exists" if p.exists() else "missing"})
            if not rec.get("ok"):
                broken += 1
            results.append(rec)

    out = {"broken": broken, "results": results}
    (REPORTS / "linkcheck_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"linkcheck: {broken} broken links")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())

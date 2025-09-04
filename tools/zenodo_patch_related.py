#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

BASE = os.environ.get("ZENODO_API", "https://zenodo.org/api")


def http_json(method: str, url: str, token: Optional[str] = None, data: Optional[dict] = None, timeout: int = 90):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            try:
                return resp.getcode(), json.loads(raw)
            except Exception:
                return resp.getcode(), raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}


def find_record_by_doi(doi: str) -> Tuple[Optional[int], dict]:
    # Try search API
    q = urllib.parse.urlencode({"q": f"doi:{doi}", "size": 1})
    url = f"{BASE}/records/?{q}"
    code, data = http_json("GET", url)
    if code == 200:
        hits = (data.get("hits", {}) or {}).get("hits", [])
        if hits:
            rec = hits[0]
            return rec.get("id"), rec
    # Fallback: numeric recid from doi suffix
    try:
        recid = int(doi.rsplit(".", 1)[-1])
        code2, rec = http_json("GET", f"{BASE}/records/{recid}")
        if code2 == 200:
            return recid, rec
        return None, {"error": f"records/{recid} lookup failed", "payload": rec}
    except Exception as e:
        return None, {"error": f"parse/fetch failed: {e}"}


def list_depositions(token: str) -> List[dict]:
    results: List[dict] = []
    page = 1
    while True:
        url = f"{BASE}/deposit/depositions?size=200&page={page}"
        code, data = http_json("GET", url, token=token)
        if code != 200:
            raise RuntimeError(f"list_depositions failed: {code} {data}")
        if not isinstance(data, list) or not data:
            break
        results.extend(data)
        if len(data) < 200:
            break
        page += 1
        if page > 5:
            break
    return results


def find_deposition_for_record(deps: List[dict], record_id: int) -> Optional[dict]:
    for d in deps:
        if d.get("record_id") == record_id:
            return d
        links = d.get("links", {}) or {}
        rec_url = links.get("record") or links.get("latest")
        if rec_url and str(record_id) in rec_url:
            return d
    return None


def ensure_draft(dep: dict, token: str) -> Tuple[str, dict, bool]:
    dep_id = str(dep.get("id"))
    state = dep.get("state")
    if state != "done":
        return dep_id, dep, False
    # create new version draft
    url_newv = f"{BASE}/deposit/depositions/{dep_id}/actions/newversion"
    code, res = http_json("POST", url_newv, token=token)
    if code not in (201, 202):
        raise RuntimeError(f"newversion failed for {dep_id}: {code} {res}")
    latest_draft = (res.get("links", {}) or {}).get("latest_draft")
    if not latest_draft:
        raise RuntimeError("latest_draft link missing after newversion")
    new_id = latest_draft.rstrip("/").split("/")[-1]
    code2, dep2 = http_json("GET", f"{BASE}/deposit/depositions/{new_id}", token=token)
    if code2 != 200:
        raise RuntimeError(f"fetch new draft {new_id} failed: {code2} {dep2}")
    return new_id, dep2, True


def parse_add(s: str) -> dict:
    # format: relation=isPartOf,identifier=10.5281/zenodo.16533373,scheme=doi
    parts = {}
    for kv in s.split(","):
        if "=" in kv:
            k, v = kv.split("=", 1)
            parts[k.strip()] = v.strip()
    if not parts.get("relation") or not parts.get("identifier"):
        raise ValueError("--add requires relation=... and identifier=...")
    if not parts.get("scheme"):
        parts["scheme"] = "doi"
    return parts


def patch_related(dep_id: str, token: str, additions: List[dict]) -> Tuple[int, dict]:
    url_get = f"{BASE}/deposit/depositions/{dep_id}"
    code, detail = http_json("GET", url_get, token=token)
    if code != 200:
        return code, {"error": "fetch deposition failed", "detail": detail}
    md = detail.get("metadata") or {}
    current = md.get("related_identifiers") or []
    # dedupe
    def k(x):
        rel = x.get("relation") or (x.get("relation_type") or {}).get("id")
        return (x.get("identifier"), rel, x.get("scheme"))
    have = {k(x) for x in current}
    merged = list(current)
    for a in additions:
        if k(a) not in have:
            merged.append(a)
            have.add(k(a))
    payload = {"metadata": {"related_identifiers": merged}}
    return http_json("PUT", url_get, token=token, data=payload)


def publish(dep_id: str, token: str) -> Tuple[int, dict]:
    return http_json("POST", f"{BASE}/deposit/depositions/{dep_id}/actions/publish", token=token)


def main() -> int:
    ap = argparse.ArgumentParser(description="Patch related_identifiers on a Zenodo record by DOI")
    ap.add_argument("--doi", required=True, help="Target DOI (e.g., 10.5281/zenodo.17053446)")
    ap.add_argument("--add", action="append", default=[], help="Add relation, e.g., relation=isPartOf,identifier=10.5281/zenodo.16533373,scheme=doi")
    ap.add_argument("--token", default=os.environ.get("ZENODO_TOKEN"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    if not args.add:
        print("ERROR: provide at least one --add", file=sys.stderr)
        return 2
    additions = [parse_add(s) for s in args.add]

    rec_id, rec = find_record_by_doi(args.doi)
    plan = {"record": {"doi": args.doi, "record_id": rec_id, "found": bool(rec_id)}, "additions": additions}
    if not rec_id:
        print(json.dumps(plan, indent=2))
        return 1

    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return 0
    if not args.token:
        print("ERROR: ZENODO_TOKEN missing; set env or pass --token", file=sys.stderr)
        return 2

    deps = list_depositions(args.token)
    dep = find_deposition_for_record(deps, rec_id)
    if not dep:
        plan["error"] = "deposition not found in your account"
        print(json.dumps(plan, indent=2))
        return 1

    dep_id, dep_detail, created = ensure_draft(dep, args.token)
    code, res = patch_related(dep_id, args.token, additions)
    out = {"patched": {"dep_id": dep_id, "code": code, "resp": res}}
    if args.publish:
        pc, pr = publish(dep_id, args.token)
        out["published"] = {"code": pc, "resp": pr}
    print(json.dumps(out, indent=2))
    return 0 if code in (200, 201) else 1


if __name__ == "__main__":
    sys.exit(main())


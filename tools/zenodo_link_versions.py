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
    # First try search API
    q = urllib.parse.urlencode({"q": f"doi:{doi}", "size": 1})
    url = f"{BASE}/records/?{q}"
    code, data = http_json("GET", url)
    if code == 200:
        hits = (data.get("hits", {}) or {}).get("hits", [])
        if hits:
            rec = hits[0]
            return rec.get("id"), rec
    # Fallback: parse numeric recid from DOI suffix and fetch directly
    try:
        recid = int(doi.rsplit(".", 1)[-1])
        code2, rec = http_json("GET", f"{BASE}/records/{recid}")
        if code2 == 200:
            return recid, rec
        return None, {"error": f"records/{recid} lookup failed", "payload": rec}
    except Exception as e:
        return None, {"error": f"parse/fetch failed: {e}"}


def list_depositions(token: str) -> List[dict]:
    # Paginate if needed (cap at 1000)
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
        # Fallback via links.record
        links = d.get("links", {}) or {}
        rec_url = links.get("record") or links.get("latest")
        if rec_url and str(record_id) in rec_url:
            return d
    return None


def merge_related_identifiers(current: List[dict], additions: List[dict]) -> List[dict]:
    out = list(current or [])
    def key(x):
        return (x.get("identifier"), x.get("relation") or (x.get("relation_type") or {}).get("id"), x.get("scheme"))
    have = {key(x) for x in out}
    for a in additions:
        if key(a) not in have:
            out.append(a)
            have.add(key(a))
    return out


def patch_related_identifiers(dep_id: str, token: str, additions: List[dict]) -> Tuple[int, dict]:
    url_get = f"{BASE}/deposit/depositions/{dep_id}"
    code, detail = http_json("GET", url_get, token=token)
    if code != 200:
        return code, {"error": "fetch deposition failed", "detail": detail}
    md = detail.get("metadata") or {}
    current = md.get("related_identifiers") or []
    merged = merge_related_identifiers(current, additions)
    payload = {"metadata": {"related_identifiers": merged}}
    return http_json("PUT", url_get, token=token, data=payload)


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


def publish_draft(dep_id: str, token: str) -> Tuple[int, dict]:
    url = f"{BASE}/deposit/depositions/{dep_id}/actions/publish"
    return http_json("POST", url, token=token)


def main() -> int:
    ap = argparse.ArgumentParser(description="Link Zenodo records as versions via related_identifiers")
    ap.add_argument("--doi-new", required=True, help="DOI of the new version (e.g., 10.5281/zenodo.16921952)")
    ap.add_argument("--doi-old", required=True, help="DOI of the previous version (e.g., 10.5281/zenodo.16682784)")
    ap.add_argument("--doi-concept", required=True, help="Concept DOI (aggregator)")
    ap.add_argument("--token", default=os.environ.get("ZENODO_TOKEN"), help="Zenodo access token (or set ZENODO_TOKEN)")
    ap.add_argument("--publish", action="store_true", help="Publish drafts after patching")
    ap.add_argument("--dry-run", action="store_true", help="Do not modify, just print plan")
    args = ap.parse_args()

    if not args.token and not args.dry_run:
        print("ERROR: ZENODO_TOKEN not set and --token not provided", file=sys.stderr)
        return 2

    # Resolve records by DOI (no auth)
    rec_new_id, rec_new = find_record_by_doi(args.doi_new)
    rec_old_id, rec_old = find_record_by_doi(args.doi_old)
    plan = {
        "records": {
            "new": {"doi": args.doi_new, "record_id": rec_new_id, "found": bool(rec_new_id)},
            "old": {"doi": args.doi_old, "record_id": rec_old_id, "found": bool(rec_old_id)},
            "concept": {"doi": args.doi_concept},
        },
        "actions": []
    }
    if not rec_new_id or not rec_old_id:
        plan["error"] = "Could not resolve one or both DOIs to record IDs"
        print(json.dumps(plan, indent=2))
        return 1

    # Compute additions
    add_new = [
        {"identifier": args.doi_old, "relation": "isNewVersionOf", "scheme": "doi"},
        {"identifier": args.doi_concept, "relation": "isPartOf", "scheme": "doi"},
    ]
    add_old = [
        {"identifier": args.doi_new, "relation": "isPreviousVersionOf", "scheme": "doi"},
        {"identifier": args.doi_concept, "relation": "isPartOf", "scheme": "doi"},
    ]

    if args.dry_run:
        plan["actions"].append({
            "target": "new",
            "record_id": rec_new_id,
            "additions": add_new,
        })
        plan["actions"].append({
            "target": "old",
            "record_id": rec_old_id,
            "additions": add_old,
        })
        print(json.dumps(plan, indent=2))
        return 0

    # Authenticated: locate depositions for these records
    deps = list_depositions(args.token)
    dep_new = find_deposition_for_record(deps, rec_new_id)
    dep_old = find_deposition_for_record(deps, rec_old_id)
    if not dep_new or not dep_old:
        plan["error"] = "Could not find depositions for one or both records in your account"
        plan["depositions_found"] = {"new": bool(dep_new), "old": bool(dep_old)}
        print(json.dumps(plan, indent=2))
        return 1

    # Ensure drafts
    dep_new_id, dep_new_detail, created_new = ensure_draft(dep_new, args.token)
    dep_old_id, dep_old_detail, created_old = ensure_draft(dep_old, args.token)

    # Patch related_identifiers
    code1, res1 = patch_related_identifiers(dep_new_id, args.token, add_new)
    code2, res2 = patch_related_identifiers(dep_old_id, args.token, add_old)

    result = {
        "patched": {
            "new": {"dep_id": dep_new_id, "code": code1, "resp": res1},
            "old": {"dep_id": dep_old_id, "code": code2, "resp": res2},
        },
        "published": {}
    }

    # Optionally publish
    if args.publish:
        p1c, p1 = publish_draft(dep_new_id, args.token)
        p2c, p2 = publish_draft(dep_old_id, args.token)
        result["published"] = {"new": {"code": p1c, "resp": p1}, "old": {"code": p2c, "resp": p2}}

    print(json.dumps(result, indent=2))
    # Return non-zero if any patch failed
    exit_code = 0
    if code1 not in (200, 201) or code2 not in (200, 201):
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

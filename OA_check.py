#!/usr/bin/env python3
"""
oa_check.py  –  consulta disponibilidade Open Access no Unpaywall
uso:  python oa_check.py refs_raw.bib  --email you@example.com
"""

import argparse, csv, time, requests, bibtexparser, pandas as pd
API_BASE = "https://api.unpaywall.org/v2/"

def load_dois(bib_path: str) -> list[str]:
    with open(bib_path, encoding="utf-8") as fh:
        bib_db = bibtexparser.load(fh)
    return [entry["doi"].lower() for entry in bib_db.entries if "doi" in entry]

def query_unpaywall(doi: str, email: str) -> dict:
    url = f"{API_BASE}{doi}"
    rsp = requests.get(url, params={"email": email}, timeout=10)
    if rsp.status_code != 200:
        return {"doi": doi, "status": "error", "http": rsp.status_code}
    data = rsp.json()
    best_oa = data.get("best_oa_location") or {}
    return {
        "doi": doi,
        "title": data.get("title", "")[:120],
        "is_oa": data.get("is_oa"),
        "oa_status": data.get("oa_status"),
        "license": best_oa.get("license"),
        "url": best_oa.get("url_for_pdf") or best_oa.get("url"),
        "published_date": data.get("published_date"),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bibfile", help="BibTeX file with DOI fields")
    ap.add_argument("--email", required=True, help="contact e‑mail for Unpaywall")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between queries")
    args = ap.parse_args()

    dois = load_dois(args.bibfile)
    rows = []
    for doi in dois:
        rows.append(query_unpaywall(doi, args.email))
        time.sleep(args.delay)

    df = pd.DataFrame(rows)
    out_csv = "oa_status.csv"
    df.to_csv(out_csv, index=False)
    print(f"✓ Resultado salvo em {out_csv}")

if __name__ == "__main__":
    main()
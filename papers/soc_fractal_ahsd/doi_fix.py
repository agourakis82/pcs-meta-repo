#!/usr/bin/env python3
"""
doi_fix.py  –  Valida e corrige DOIs usando a API Crossref
uso: python doi_fix.py refs_raw.bib
"""
import re, json, time, requests, bibtexparser, csv, copy, sys, pathlib

API = "https://api.crossref.org/works"

def slug(s):                     # normaliza strings para comparação
    return re.sub(r'\W+', '', s.lower())

def guess_doi(title):
    params = {"query.title": title, "rows": 1}
    r = requests.get(API, params=params, timeout=10)
    if r.status_code != 200 or not r.json()["message"]["items"]:
        return None
    return r.json()["message"]["items"][0]["DOI"].lower()

def main(bibfile):
    path = pathlib.Path(bibfile)
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)

    report = []
    updated = False

    for entry in db.entries:
        title = entry.get("title", "")
        if not title:
            continue
        doi_old = entry.get("doi", "").lower().strip()
        doi_new = guess_doi(title)

        if not doi_new:
            report.append([entry["ID"], "não encontrado", doi_old, ""])
            continue

        if doi_old == doi_new:
            report.append([entry["ID"], "ok", doi_old, ""])
        else:
            entry["doi"] = doi_new
            updated = True
            report.append([entry["ID"], "corrigido", doi_old, doi_new])

        time.sleep(0.5)          # respeita rate‑limit Crossref

    if updated:
        backup = path.with_suffix(".bak")
        path.replace(backup)
        with open(path, "w", encoding="utf-8") as f:
            bibtexparser.dump(db, f)
        print(f"✓ BibTeX atualizado; backup salvo em {backup}")

    with open("doi_report.csv", "w", newline="", encoding="utf-8") as out:
        csv.writer(out).writerows(
            [["ID", "status", "doi_antigo", "doi_novo"]] + report
        )
    print("✓ Relatório salvo em doi_report.csv")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python doi_fix.py refs_raw.bib"); sys.exit(1)
    main(sys.argv[1])
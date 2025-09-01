#!/usr/bin/env python3
"""Offline link extractor for Markdown files."""
import json
import re
from pathlib import Path

MD_LINK_RE = re.compile(r"\[(.*?)\]\((http[s]?://[^\)]+)\)")
MAX_LINKS = 20


def main():
    results = {}
    count = 0
    for md_path in Path(".").rglob("*.md"):
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        links = MD_LINK_RE.findall(text)
        link_status = []
        for _, url in links:
            link_status.append({"url": url, "status": "unchecked"})
            count += 1
            if count >= MAX_LINKS:
                break
        if link_status:
            results[str(md_path)] = link_status
        if count >= MAX_LINKS:
            break
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

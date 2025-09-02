"""
Token normalization helper (v4.3)
- lowercases
- strips punctuation/underscores
- removes accents (unicode combining marks)
"""
from __future__ import annotations
import re
import unicodedata
from typing import Optional

def deaccent(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def token_norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    if not isinstance(s, str):
        s = str(s)
    s = deaccent(s.lower())
    s = re.sub(r"[\W_]+", "", s)
    return s or None

if __name__ == "__main__":
    tests = ["Café", "Hello, world!", "co-operate", None, 123]
    for t in tests:
        print(t, "->", token_norm(t))

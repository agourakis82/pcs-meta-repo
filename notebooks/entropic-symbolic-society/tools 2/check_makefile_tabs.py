#!/usr/bin/env python3
import pathlib
import re
import sys

mk = pathlib.Path("Makefile")
if not mk.exists():
    sys.exit(0)

lines = mk.read_text(encoding="utf-8", errors="ignore").splitlines()
errs = []
in_rule = False

rule_re = re.compile(r"^[A-Za-z0-9_.\-/]+(?:\s*[:,].*)?$")  # alvo: “target: deps”
for i, L in enumerate(lines, start=1):
    if not L.strip() or L.lstrip().startswith("#"):
        continue

    # detecta começo de regra (linha com “target:”)
    if rule_re.match(L) and ":" in L and not L.startswith("\t"):
        in_rule = True
        continue

    # se estamos dentro de uma regra, toda receita não-vazia deve começar com TAB
    if in_rule:
        if L.strip() and not L.startswith("\t"):
            errs.append(
                f"Linha {i}: receita deve iniciar com TAB, não espaços -> {L[:40]!r}"
            )
        # sai do bloco da regra quando encontramos nova regra
        if rule_re.match(L) and ":" in L and not L.startswith("\t"):
            in_rule = True  # próxima regra
        # heurística simples: se aparece algo que não é receita nem comentário,
        # mantemos o estado; o erro acima já cobre receitas iniciadas com espaço.

# Reporta
if errs:
    print("Erro: Makefile contém receitas sem TAB:")
    for e in errs:
        print("  -", e)
    sys.exit(1)
sys.exit(0)

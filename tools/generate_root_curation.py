#!/usr/bin/env python3
"""
Scan the repository root for top-level files and produce a CURATION_INDEX.yaml
with a recommended action for each file (keep/move/archive/ignore) and target.

Heuristics only use stdlib and filename patterns to stay safe and portable.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


TOP_DIRS_KEEP = {
    ".git",
    ".venv",
    ".vscode",
    ".vscode-server",
    "src",
    "api",
    "scripts",
    "tests",
    "config",
    "docs",
    "ops",
    "ragpp",
    "services",
    "notebooks",
    "reports",
    "data",
    "models",
    "logs",
    "static",
    "ssl",
}


# Pattern -> (category, action, target)
RULES = [
    # Logs and caches
    (r".*\.(log)$", ("log", "move", "logs/")),
    (r"^(\.pytest_cache|\.mypy_cache|\.ruff_cache)$", ("cache", "ignore", None)),
    # Zip/artifacts/downloads
    (r".*\.(zip|tar|gz|bz2|xz)$", ("artifact", "move", "artifacts/")),
    (r".*Zone\.Identifier$", ("windows_stream", "archive", "attic/windows_streams/")),
    # Tests and quick scripts
    (r"^(test_.*\.(py|sh|md)|tests?-.*|.*_test\.py)$", ("test", "move", "tests/")),
    # Runner scripts
    (r"^(run_.*|RUN_.*|execute_.*|EXECUTE_.*)\.(py|sh)$", ("runner", "move", "scripts/")),
    # Ops/maintenance scripts
    (r"^(apply_.*|diagnose_.*|fix_.*|cleanup_.*|configure_.*|setup_.*)\.(py|sh|ps1|bat)$",
     ("ops_script", "move", "ops/")),
    # Build/deploy/release
    (r"^(build_.*)\.(py|sh)$", ("build_script", "move", "scripts/")),
    (r"^(deploy_.*|release_.*)\.(py|sh)$", ("deploy_script", "move", "ops/")),
    # Setup/ops scripts
    (r"^(setup_.*|install_.*|deploy_.*|update_.*|backup_.*|restore_.*)\.(py|sh|ps1|bat)$",
     ("ops_script", "move", "ops/")),
    # Config and services
    (r".*\.(service|conf|ini)$", ("service_config", "move", "ops/")),
    (r".*\.(yml|yaml)$", ("config", "move", "config/")),
    # Metadata / citations / release
    (r"^(zenodo.*|\.zenodo.*|CITATION.*|metadata.*|PROVENANCE\.yaml)$",
     ("metadata", "move", "metadata/")),
    # Docs / READMEs / reports
    (r"^(README.*|CHANGELOG.*|RELEASE_NOTES.*|CONTRIBUTING.*|CODE_OF_CONDUCT.*|SECURITY.*|QUALITY_GATES.*|LICENSE.*|GUIDE.*|GUIA_.*|RELATORIO_.*|REPORT.*|.*_SUMMARY\.md|.*_REPORT\.md|.*_PLAN\.md)$",
     ("docs", "move", "docs/")),
    (r"^.*GUIDE.*\.md$", ("docs", "move", "docs/")),
    (r"^.*SUMMARY.*\.md$", ("docs", "move", "docs/")),
    (r"^(SWOW_.*|EEG_.*|COMPREHENSIVE_.*|OVERFITTING_.*|final_.*|cross_.*|.*SUMMARY.*|.*REPORT.*)\.md$",
     ("docs_report", "move", "reports/")),
    # Packaging/build specs
    (r".*\.(spec)$", ("packaging", "move", "packaging/")),
    # Miscellaneous temp files
    (r"^(000000|out|outputs|runs|temp_.*)$", ("temp", "move", "artifacts/")),
]


@dataclass
class Entry:
    path: str
    type: str
    action: str
    target: Optional[str]
    reason: str


def classify(filename: str) -> Optional[Entry]:
    # Defaults for known top-level essentials (checked first)
    essentials = {
        "pyproject.toml": ("build", "keep", None),
        "requirements.txt": ("build", "keep", None),
        "requirements-web.txt": ("build", "keep", None),
        "Dockerfile": ("build", "keep", None),
        "Makefile": ("build", "keep", None),
        "pytest.ini": ("test_config", "keep", None),
        ".pre-commit-config.yaml": ("dev_config", "keep", None),
        ".jupytext.toml": ("dev_config", "keep", None),
        ".editorconfig": ("dev_config", "keep", None),
        ".gitignore": ("vcs", "keep", None),
        ".gitattributes": ("vcs", "keep", None),
        ".github": ("ci", "keep", None),
        ".markdownlintignore": ("dev_config", "keep", None),
        ".markdownlint.json.disabled": ("dev_config", "keep", None),
        "CODEOWNERS": ("meta", "keep", None),
        "LICENSE": ("license", "keep", None),
        "LICENSES": ("license", "keep", None),
        "README.md": ("docs", "keep", None),
        "SECURITY.md": ("docs", "keep", None),
        "CODE_OF_CONDUCT.md": ("docs", "keep", None),
        "CONTRIBUTING.md": ("docs", "keep", None),
        "CITATION.cff": ("citation", "keep", None),
    }
    if filename in essentials:
        t, a, target = essentials[filename]
        return Entry(path=filename, type=t, action=a, target=target, reason="Essential file")

    # Then apply general rules
    for pattern, (category, action, target) in RULES:
        if re.match(pattern, filename, flags=re.IGNORECASE):
            return Entry(
                path=filename,
                type=category,
                action=action,
                target=target,
                reason=f"Matched rule {pattern}",
            )
    # If still not matched, check if it belongs to metadata family
    # Unknown: suggest archive if top-level and not a directory
    return Entry(path=filename, type="unknown", action="review", target=None, reason="No rule matched")


def list_root_files(root: str) -> List[str]:
    entries: List[str] = []
    for name in sorted(os.listdir(root)):
        if name in TOP_DIRS_KEEP:
            continue
        # Keep hidden/dev/control dirs but don't try to classify them as files
        full = os.path.join(root, name)
        if os.path.isdir(full):
            continue
        entries.append(name)
    return entries


def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def dump_yaml(entries: List[Entry], out_path: str) -> None:
    ensure_dir(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated by tools/generate_root_curation.py\n")
        f.write("# action: keep | move | archive | ignore | review\n")
        f.write("items:\n")
        for e in entries:
            f.write(f"  - path: {e.path}\n")
            f.write(f"    type: {e.type}\n")
            f.write(f"    action: {e.action}\n")
            if e.target:
                f.write(f"    target: {e.target}\n")
            f.write(f"    reason: {e.reason}\n")


def dump_summary(entries: List[Entry], out_path: str) -> None:
    # Aggregate counts by action and target
    by_action = {}
    by_target = {}
    for e in entries:
        by_action[e.action] = by_action.get(e.action, 0) + 1
        key = e.target or "-"
        by_target[key] = by_target.get(key, 0) + 1

    lines: List[str] = []
    lines.append("# Curadoria da raiz do repositório")
    lines.append("")
    lines.append("Este relatório resume a análise automática dos arquivos soltos na raiz.")
    lines.append("Os critérios são heurísticos e servem como ponto de partida para revisão humana.")
    lines.append("")
    lines.append("## Resumo")
    lines.append("")
    lines.append(f"- Total de entradas analisadas: {len(entries)}")
    lines.append("- Ações sugeridas:")
    for action, cnt in sorted(by_action.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  - {action}: {cnt}")
    lines.append("- Destinos sugeridos:")
    for target, cnt in sorted(by_target.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  - {target}: {cnt}")
    lines.append("")
    lines.append("## Próximos passos sugeridos")
    lines.append("")
    lines.append("- Conferir itens com ação 'review' e decidir destino.")
    lines.append("- Mover logs para `logs/` e adicionar ao `.gitignore` se necessário.")
    lines.append("- Mover artefatos (`*.zip`) para `artifacts/` ou publicar em releases.")
    lines.append("- Centralizar metadados (Zenodo/CITATION/metadata) em `metadata/`.")
    lines.append("- Scripts `run_*` e `setup_*` para `scripts/` ou `ops/` conforme o caso.")
    lines.append("- Consolidar READMEs/CHANGELOGs em `docs/` e relatórios em `reports/`.")
    lines.append("")
    lines.append("> Arquivo gerado por `tools/generate_root_curation.py`.")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    root = REPO_ROOT
    files = list_root_files(root)
    entries = [classify(fn) for fn in files]
    out_yaml = os.path.join(root, "CURATION_INDEX.yaml")
    dump_yaml(entries, out_yaml)
    out_md = os.path.join(root, "CURADORIA_RAIZ.md")
    dump_summary(entries, out_md)
    print(f"Wrote {out_yaml} with {len(entries)} entries.")
    print(f"Wrote {out_md} summary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

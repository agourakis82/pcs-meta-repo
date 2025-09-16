#!/usr/bin/env python3
"""
Build and store a "Project Memory Pack" so ChatGPT and other AIs can
recall PCS project knowledge via RAG++ Extended Memory.

What it does
- Scans key repo files (docs, config, servers) and compiles:
  - Project overview (structure, languages, key components)
  - FastAPI endpoints (paths/methods)
  - MCP tools (names/descriptions)
  - Key docs excerpts (README, selected docs)
- Stores each section as project contexts in ExtendedMemoryService.

Usage
  python scripts/build_project_memory.py \
      --project-name pcs-meta-repo \
      [--docs-limit 6] [--excerpt-bytes 3000]

After this, you can recall context via:
- REST:   GET /memory/chatgpt/recall?query=... (see ragpp_web_server.py)
- MCP:    tool "search" with target="memory" (alias) or your own tools
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_text_safe(p: Path, limit_bytes: int | None = None) -> str:
    try:
        data = p.read_bytes()
        if limit_bytes is not None:
            data = data[: max(0, limit_bytes)]
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def collect_overview() -> str:
    files = [p for p in REPO_ROOT.rglob("*") if p.is_file()]
    by_ext = Counter([p.suffix.lower() for p in files])
    top_ext = ", ".join(f"{ext or '(no-ext)'}:{cnt}" for ext, cnt in by_ext.most_common(8))

    key_dirs = [
        "ragpp",
        "src",
        "scripts",
        "config",
        "docs",
        "notebooks",
        "nginx",
        "cloudflared",
    ]
    dir_counts = {}
    for d in key_dirs:
        p = REPO_ROOT / d
        if p.exists():
            dir_counts[d] = sum(1 for _ in p.rglob("*") if _.is_file())

    lines = [
        "PCS Project Memory Pack — Overview",
        "",
        f"Total files: {len(files)}",
        f"Top extensions: {top_ext}",
        "Key directories (file counts):",
    ]
    for d, c in dir_counts.items():
        lines.append(f"- {d}: {c}")

    # Mention server components if present
    web_server = REPO_ROOT / "ragpp" / "ragpp_web_server.py"
    mcp_server = REPO_ROOT / "ragpp" / "ragpp_mcp_server.py"
    if web_server.exists():
        lines.append(f"Web Server: {web_server.relative_to(REPO_ROOT)}")
    if mcp_server.exists():
        lines.append(f"MCP Server: {mcp_server.relative_to(REPO_ROOT)}")

    return "\n".join(lines)


def collect_fastapi_endpoints(server_path: Path) -> str:
    src = _read_text_safe(server_path, None)
    if not src:
        return "No endpoints found (file not readable)."

    # Rough extraction of FastAPI routes
    routes: List[Tuple[str, str]] = []
    for m in re.finditer(r"@app\.(get|post|put|delete|patch)\(\s*(['\"])(/[^'\"]*)\2", src):
        method = m.group(1).upper()
        path = m.group(3)
        routes.append((method, path))

    # Deduplicate and sort
    uniq = sorted(set(routes), key=lambda x: (x[1], x[0]))
    lines = [
        f"FastAPI Endpoints ({server_path.relative_to(REPO_ROOT)}):",
    ]
    for method, path in uniq:
        lines.append(f"- {method} {path}")
    if not uniq:
        lines.append("(none detected)")
    return "\n".join(lines)


def collect_mcp_tools(mcp_path: Path) -> str:
    src = _read_text_safe(mcp_path, None)
    if not src:
        return "No MCP tools found (file not readable)."

    # Capture Tool(name="...", description="...") pairs
    tools: List[Tuple[str, str]] = []
    for m in re.finditer(
        r"Tool\(\s*name\s*=\s*['\"]([^'\"]+)['\"]\s*,\s*description\s*=\s*['\"]([^'\"]+)['\"]",
        src,
    ):
        tools.append((m.group(1), m.group(2)))

    lines = [
        f"MCP Tools ({mcp_path.relative_to(REPO_ROOT)}):",
    ]
    for name, desc in tools:
        lines.append(f"- {name}: {desc}")
    if not tools:
        lines.append("(none detected)")
    return "\n".join(lines)


def collect_key_docs(max_docs: int, excerpt_bytes: int) -> List[Tuple[str, str]]:
    # Prioritize central docs
    candidates: List[Path] = []
    for rel in [
        Path("README.md"),
        Path("docs/EXTENDED_MEMORY_GUIDE.md"),
        Path("ragpp/SETUP_COMPLETE_SUMMARY.md"),
        Path("RAGPP_FINAL_COMPLETE.md"),
        Path("docs/EXECUTION_STEPS_v4.4.md"),
        Path("docs/NATURE_Q1_ENHANCEMENT_PLAN.md"),
        Path("docs/NATURE_HUMAN_BEHAVIOUR_ENHANCEMENT_PLAN.md"),
    ]:
        p = REPO_ROOT / rel
        if p.exists():
            candidates.append(p)

    # Add a few more markdowns from docs/
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        md_docs = sorted(docs_dir.glob("*.md"))
        for p in md_docs:
            if p not in candidates:
                candidates.append(p)

    # Include selected ops/ guides if present
    ops_dir = REPO_ROOT / "ops"
    if ops_dir.exists():
        for name in [
            "IMPLEMENTATION_COMPLETE.md",
            "DATA_ANALYSIS_SYSTEM_GUIDE.md",
            "AUDIT_AND_FIX.md",
        ]:
            p = ops_dir / name
            if p.exists() and p not in candidates:
                candidates.append(p)

    # Limit
    selected = candidates[:max_docs]
    result: List[Tuple[str, str]] = []
    for p in selected:
        text = _read_text_safe(p, excerpt_bytes)
        if text:
            header = f"Doc excerpt: {p.relative_to(REPO_ROOT)}"
            result.append((header, text))
    return result


def main():
    parser = argparse.ArgumentParser(description="Build and store PCS Project Memory Pack")
    parser.add_argument("--project-name", default="pcs-meta-repo")
    parser.add_argument("--docs-limit", type=int, default=6)
    parser.add_argument("--excerpt-bytes", type=int, default=3000)
    args = parser.parse_args()

    # Import memory service lazily (local path import)
    sys.path.append(str((REPO_ROOT / "ragpp").resolve()))
    try:
        from extended_memory_service import get_memory_service  # type: ignore
    except Exception:
        # Try package-style import
        sys.path.append(str(REPO_ROOT.resolve()))
        from ragpp.extended_memory_service import get_memory_service  # type: ignore

    memory = get_memory_service()

    # 1) Overview
    overview = collect_overview()
    memory.store_project_context(
        project_name=args.project_name,
        context_type="overview",
        content=overview,
        metadata={"source": "build_project_memory.py"},
    )

    # 2) FastAPI endpoints
    web_server = REPO_ROOT / "ragpp" / "ragpp_web_server.py"
    if web_server.exists():
        endpoints = collect_fastapi_endpoints(web_server)
        memory.store_project_context(
            project_name=args.project_name,
            context_type="endpoints",
            content=endpoints,
            metadata={"file": str(web_server.relative_to(REPO_ROOT))},
        )

    # 3) MCP tools
    mcp_server = REPO_ROOT / "ragpp" / "ragpp_mcp_server.py"
    if mcp_server.exists():
        mcp_tools = collect_mcp_tools(mcp_server)
        memory.store_project_context(
            project_name=args.project_name,
            context_type="mcp_tools",
            content=mcp_tools,
            metadata={"file": str(mcp_server.relative_to(REPO_ROOT))},
        )

    # 4) Key docs excerpts
    for header, excerpt in collect_key_docs(args.docs_limit, args.excerpt_bytes):
        memory.store_project_context(
            project_name=args.project_name,
            context_type="doc_excerpt",
            content=f"{header}\n\n{excerpt}",
            metadata={"kind": "excerpt"},
        )

    print("✅ Project Memory Pack stored in Extended Memory Service")


if __name__ == "__main__":
    main()

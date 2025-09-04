# Agentic Design Patterns — PCS-HELIO v4.3 (Symbolic First)

**Author:** Demetrios Agourakis · ORCID 0000-0002-8596-5097  
**Collaborator (Data Science & AI):** Dionisio Chiuratto Agourakis  
**License:** CC BY 4.0  
**Version:** v4.3 · 2025-09-04  

---

## Purpose
Integrate Agentic Prompt Design into the PCS-HELIO pipeline, reinforcing traceability, auditability, and consistency across prompts (Codex/5-pro), notebooks, scripts, and manuscripts.

## Agentic 5-Step Pattern
1. **Planner** — objective, variables, time windows, corpus, version.  
2. **Router** — strategy selection (RAG, code, clinical analysis, deep research).  
3. **Tool-Use** — concrete execution (notebook/script/query) with logs & hashes.  
4. **Self-Reflection** — internal checks against Quality Gates (Q1–Q10).  
5. **Evaluator** — auditable output linked to DOI/version.

## Repository Integration
- **Notebooks (01–05):** annotate cells with the 5 steps.  
- **Scripts (`/src`, `/tools`):** header = Planner/Router; footer = Self-Reflection/Evaluator.  
- **Docs:** this file is referenced by `QUALITY_GATES.md` as Auxiliary Gate Q11.

## Output Contract
Include in every deliverable:
- **Version + Date** (YYYY-MM-DD)  
- **Source/DOI** when applicable  
- **Fixed seeds/env** (reproducibility)  
- **Checklist Q1–Q10 + Q11**

## Links to Governance
- Extended Memory v4.3 snapshot (authoritative plan)  
- Deep Research Runbook (Symbolic First)  
- Project Instructions v4.3 (Symbolic First)

> HELIO (SEA/VAR exogenous) is deferred to phase H1; this document applies to phase S1 (*Symbolic First*).

# Prompt Engineering Playbook — PCS (5‑Pro, RAG++)

## Principles
- State constraints & outputs explicitly (files, formats, length).
- Separate Evidence vs Plausibility vs Speculation in outputs.
- Ask for auditable synthesis (steps, criteria, numbered sources).

## Patterns
- **Deep Research (5‑Pro):** SYSTEM non-negotiables; scope; deliverables; word limits.
- **Figure Spec:** “Return fig_plan.md with panels, axes, transforms, sample sizes, caption ≥120 words.”
- **IMRaD Draft:** “Produce intro_methods.tex ≤1500 words with \cite{} to references.bib.”
- **RAG++ Query:** “Use repo-only sources; attach repo-relative citations.”

## Guardrails
- No PII; public data only; licenses respected.
- No hidden chain-of-thought; provide steps + sources.
- Fixed seeds; versions & dates for sources.

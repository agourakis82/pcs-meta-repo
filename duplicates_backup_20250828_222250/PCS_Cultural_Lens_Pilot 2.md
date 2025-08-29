
# PCS–Cultural Lens Pilot (Public Data Only)
**Project Lead:** Demetrios Agourakis (ORCID: 0000-0002-8596-5097)
**Lineage:** Fractal Entropy — Psiquiatria Computacional‑Simbólica (NHB track)
**License:** CC BY 4.0 (code: MIT)
**Scope (Phase 1, 6–8 weeks):** Robust + exequível pilot focused on *cross‑cultural semantics* and *neuro‑linguistic correlates*, using only public datasets (SWOW; ZuCo; OpenNeuro where applicable).

## Deliverables
1. **Methods Note + Preprint**: “A Cultural Lens for Symbolic Manifolds in Psychiatry” (arXiv/OSF/Zenodo).
2. **Open Toolbox (v0.1)**: Scripts for SWOW multilingual graph metrics + alignment; ZuCo EEG features.
3. **Reproducibility Pack**: README, CITATION.cff, environment.yml, notebooks, data loaders; FAIR/BIDS‑lite.
4. **One Figure**: Cross‑lingual semantic network divergence (EN vs RP‑ES vs ZH) + EEG feature association.

## Datasets (public)
- **SWOW**: EN, NL, RP‑ES, ZH (association networks).
- **ZuCo 1.0 / 2.0**: EEG + eye‑tracking during English reading.
- **OpenNeuro (optional Phase 1b)**: Selected BIDS MRI/EEG datasets for replication/extension.

## Minimal Methods
- **Semantic graphs** from SWOW (per language): degree/clustering/modularity; entropy; curvature (Ollivier/Forman – optional v0.2).
- **Cross‑lingual alignment**: Procrustes/MUSE; compute **residual cultural component** not aligned.
- **Graph divergence**: Gromov‑Wasserstein (EGW proxy) between language networks.
- **Neuro‑linguistic link** (exploratory): regress ZuCo lexical metrics (freq/length/semantic centrality) on EEG/ET features.
- **Clinical bridge**: DSM‑5 Cultural Formulation Interview (CFI) as interpretive layer for prompts/protocols.

## Outputs for Visibility
- Preprint (PDF) + code DOI (Zenodo), project page (OSF), short thread (scientific Twitter/X), 1‑slide visual.
- Target journals (long‑term): *Nature Human Behaviour* line; interim: *Scientific Reports* / *PLOS ONE* methods note.

## Timeline (indicative)
- **Week 1–2**: Repo bootstrap; SWOW loaders; EN↔RP alignment; first graph metrics.
- **Week 3–4**: GW divergence; figure v1; ZuCo feature extraction (English).
- **Week 5–6**: Integrated analysis; robustness checks; cultural‑prompt audit set (v0.1).
- **Week 7–8**: Writing, figure polish, packaging, preprint + Zenodo.

## Risks & Mitigations
- **Non‑invariância** entre línguas → reportar explicitamente; usar alignment optimization e vignettes de ancoragem.
- **Bias de LLM** → auditoria cultural de prompts; documentação (Stochastic Parrots).
- **Generalização clínica** limitada (ZuCo=EN) → declarar escopo; planejar coleta futura ou datasets multi‑língues.

---
This document is a living plan for Phase 1. Keep it short, executable, and auditable.

# 🧠 NHB Computational Package — Symbolic Manifolds and Entropic Dynamics

![Symbolic Graph](figs/cover_symbolic_graph.png)

## 📘 Overview

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16783257.svg)](https://doi.org/10.5281/zenodo.16783257)

**This repository corresponds to version v1.6 (DOI: 10.5281/zenodo.16783257), building on v1.4/v1.5.**

This subproject contains the **full computational implementation** of the study:

> **"Symbolic Manifolds and Entropic Dynamics: A Cognitive Topology of Mental States"**

It is designed as a **reproducible analysis pipeline** for submission to *Nature Human Behaviour*, and is part of the broader research program:
> **"The Fractal Nature of an Entropically-Driven Society"**
> DOI (umbrella): [10.5281/zenodo.16730036](https://doi.org/10.5281/zenodo.16730036)

This package builds on the foundational fractal–entropic model (DOI: [10.5281/zenodo.16533374](https://doi.org/10.5281/zenodo.16533374)) and implements a structured 6‑notebook pipeline for empirical mapping of symbolic manifolds.

**Version:** v1.5
**DOI (code):** [10.5281/zenodo.16752238](https://doi.org/10.5281/zenodo.16752238)
**DOI (data):** [10.17605/OSF.IO/2AQP7](https://doi.org/10.17605/OSF.IO/2AQP7)

---

## 🔭 Project Scope

This work integrates large-scale semantic networks (SWOW) with symbolic metrics, graph theory, embeddings, and clustering to construct a dynamic and interpretable manifold of cognition. The pipeline addresses:

1. Can symbolic distances in associative space model cognitive entropy?
2. How do topological centrality and clustering reflect symbolic anchoring and curvature of thought?
3. Is it possible to derive measurable symbolic metrics that correlate with mental states?
4. Can entropic manifolds reveal hidden cognitive constraints or attractors?

---

## 🧪 Pipeline Architecture

| Notebook | Description |
|----------|-------------|
| `Notebook_01_Data_Preprocessing_and_Network_Construction.ipynb` | Load SWOW dataset, clean associations, build weighted directed graph |
| `Notebook_02_Network_Metrics.ipynb` | Compute centrality measures, strengths, PageRank, clustering coefficients |
| `Notebook_03_Generate_Embeddings.ipynb` | Generate node embeddings (SVD or Node2Vec) |
| `Notebook_04_Merge_Metrics_and_Embeddings.ipynb` | Merge symbolic metrics with embeddings into a unified dataset |
| `Notebook_05_Clustering_Analysis.ipynb` | Determine optimal cluster number via silhouette analysis, assign labels |
| `Notebook_06_UMAP_Visualization.ipynb` | Project embeddings to 2D (UMAP or PCA fallback), visualize clusters |

Outputs (CSV, NPY, PNG) are stored in `data/` and `results/` for reproducibility.

---

## 🗂 Directory Structure

```
NHB_Symbolic_Mainfold/
├── data/                      # Input datasets, intermediate and final outputs
│   └── raw/                   # Raw files from OSF (SWOW-EN, cueStats, etc.)
├── results/                   # Generated figures and plots
├── figs/                      # Manuscript figures
├── notebooks/                 # Official pipeline notebooks (01–06)
├── scripts/                   # utils.py, reset_env.sh, clean_and_commit.sh
├── NHB_main.tex                # NHB LaTeX manuscript
├── sections/                   # Manuscript sections (subproject scope)
├── supplementary.tex           # NHB supplementary material
├── requirements.txt            # Reproducible environment specification
└── README.md                   # This document
```

---

## ⚙️ Setup Instructions

1. **Clone the repository** (or download this subfolder).

2. **Download raw data** from OSF DOI [10.17605/OSF.IO/2AQP7](https://doi.org/10.17605/OSF.IO/2AQP7) and place files in:
```
data/raw/
```

3. **Create and activate environment:**
```bash
bash scripts/reset_env.sh
conda activate entropic-symbolic-mainfold   # or source .venv/bin/activate if using venv
```

4. **Launch JupyterLab:**
```bash
jupyter lab
```

5. **Run notebooks** in numerical order (01 → 06).

---

## 📎 Citation

If you use this package, please cite:

**Text citation:**
> Agourakis DC. *Symbolic Manifolds — NHB Computational Package (Notebooks 01–06)*. Zenodo; 2025. DOI: 10.5281/zenodo.16752238.

**BibTeX:**
```bibtex
@software{agourakis2025symbolic_v1_5,
 author = {Demetrios Agourakis},
 title = {Symbolic Manifolds — NHB Computational Package (Notebooks 01–06)},
 year = {2025},
 publisher = {Zenodo},
 doi = {10.5281/zenodo.16752238},
 version = {v1.5},
 url = {https://doi.org/10.5281/zenodo.16752238}
}
```

---

## 📜 License

This subproject follows the **dual licensing** defined in the root repository:

- **Code** (Python, notebooks, scripts): MIT License
- **Text and figures**: Creative Commons Attribution 4.0 International (CC BY 4.0)

See the root `LICENSE` file for full terms.

---

## 🧠 Author and Affiliation

Developed by **Demetrios Agourakis**
São Leopoldo Mandic / PUC-SP
ORCID: [0000-0002-8596-5097](https://orcid.org/0000-0002-8596-5097)

---

For related files, companion repositories, and datasets, refer to the [main Zenodo registry](https://doi.org/10.5281/zenodo.16730036).

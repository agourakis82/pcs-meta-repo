[![Concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16533373.svg)](https://doi.org/10.5281/zenodo.16533373)

# PCS Meta-Repo

[![CI](https://github.com/agourakis82/pcs-meta-repo/actions/workflows/python-tests.yml/badge.svg)](https://github.com/agourakis82/pcs-meta-repo/actions/workflows/python-tests.yml)
[![Coverage](coverage.svg)](coverage.svg)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--8596--5097-brightgreen.svg?logo=orcid)](https://orcid.org/0000-0002-8596-5097)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Meta-repository for the Computational‑Symbolic Psychiatry (PCS) project.

## v4.3 Highlights

- **Agentic Design Patterns** integrados como **Quality Gate Q11** (docs/agentic_design_patterns.md).

## Install & use

```bash
git clone https://github.com/agourakis82/pcs-meta-repo
cd pcs-meta-repo
pip install -r requirements.txt
```

## Quick Start

5. Follow **Agentic Design Patterns** (docs/agentic_design_patterns.md) to structure prompts, notebooks and scripts.

## How to cite

Please cite using the metadata in [CITATION.cff](CITATION.cff). Until the v4.3.2.2 DOI is minted, use the concept/aggregator DOI:

> Agourakis, Demetrios Chiuratto; Agourakis, Dionisio Chiuratto. PCS Meta-Repo — v4.3.2.2. Concept DOI: [10.5281/zenodo.16533373](https://doi.org/10.5281/zenodo.16533373)

Previous versions: v4.3.2.1 [10.5281/zenodo.17059024](https://doi.org/10.5281/zenodo.17059024); v4.3.2 [10.5281/zenodo.17053446](https://doi.org/10.5281/zenodo.17053446). Origin: [10.5281/zenodo.16682784](https://doi.org/10.5281/zenodo.16682784).

### DOI (Extended Memory consolidation)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16533374.svg)](https://doi.org/10.5281/zenodo.16533374)

Nota: a versão v4.3 unifica e substitui a v4.2 do artefato “Extended Memory — PhD & Publication Plan (Brazil)”.

- Cite v4.3: [10.5281/zenodo.16921952](https://doi.org/10.5281/zenodo.16921952)
- Versão anterior (arquivada) v4.2: [10.5281/zenodo.16682784](https://doi.org/10.5281/zenodo.16682784)


## Repository structure

- docs: documentation and specs
- src: source code (MIT)
- notebooks: analysis notebooks (reproducible stubs preferred)
- data/raw_public: public raw inputs (not tracked if large)
- data/processed: derived tables/graphs
- figures: generated plots and assets
- manuscripts: papers and drafts
- reports: QA artifacts (lint, linkcheck, inventory)
- tools: maintenance and QA scripts

## License

- Code: MIT — see `LICENSE`.
- Text, docs, and figures: CC BY 4.0 — see `LICENSES/CC-BY-4.0.txt`.

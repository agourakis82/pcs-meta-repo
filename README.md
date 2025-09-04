[![Concept DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16921951.svg)](https://doi.org/10.5281/zenodo.16921951) [![Version DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17053446.svg)](https://doi.org/10.5281/zenodo.17053446)

# PCS Meta-Repo

[![CI](https://github.com/agourakis82/pcs-meta-repo/actions/workflows/python-tests.yml/badge.svg)](https://github.com/agourakis82/pcs-meta-repo/actions/workflows/python-tests.yml)
[![Coverage](coverage.svg)](coverage.svg)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--8596--5097-brightgreen.svg?logo=orcid)](https://orcid.org/0000-0002-8596-5097)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Meta-repository for the Computational‑Symbolic Psychiatry (PCS) project.

## Install & use

```bash
git clone https://github.com/agourakis82/pcs-meta-repo
cd pcs-meta-repo
pip install -r requirements.txt
```

## How to cite

Please cite using the metadata in [CITATION.cff](CITATION.cff):

> Agourakis, D. PCS Meta-Repo — v4.3.2. DOI: [10.5281/zenodo.17053446](https://doi.org/10.5281/zenodo.17053446)

For additional materials see the Zenodo concept record [10.5281/zenodo.16921951](https://doi.org/10.5281/zenodo.16921951).

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

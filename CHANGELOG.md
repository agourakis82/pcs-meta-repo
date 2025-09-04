# Changelog

## [v4.3.2] — 2025-09-04

### Changed

* Synced README badges to Concept DOI 10.5281/zenodo.16921951 and Version DOI 10.5281/zenodo.17053446.
* Updated CITATION.cff to v4.3.2 with release date and version DOI; set type=software, license=MIT, and added preferred-citation block.
* Aligned metadata.yaml and .zenodo.json to v4.3.2 and correct concept DOI.

### Added

* QA scripts: repo_lint, markdown linkcheck, and repo inventory (reports under `reports/`).
* Provenance stub at `data/provenance.yaml`.

### Fixed

* Replaced outdated DOI links; ensured no broken links in README.

### Documentation

* Added DOI consolidation note for “Extended Memory — PhD & Publication Plan (Brazil)”: v4.3 (10.5281/zenodo.16921952) supersedes v4.2 (10.5281/zenodo.16682784); both linked under concept DOI 10.5281/zenodo.16533374.

## v2025.09.02 — Zenodo release (DOI: 10.5281/zenodo.17039429)

- Notebooks 01–06 hardened (RUN_MODE sample/full, robust imports/paths)
- KEC/ZuCo pipelines stabilized; H* validator integrated
- CI: normalize notebook IDs and nbconvert with full→sample fallback (PRs = sample)
- Metadata aligned for Zenodo/CITATION (DOI badge + links)
- Repo cleanup: removed duplicate notebook-generated artifacts under `notebooks/`

## v0.1.0 — 2025-08-21

- Definitive starter pack for PCS meta-repository.

- Added docs, meta (CITATION.cff, metadata.yaml), CI, LFS.

## v0.2.0 — Unificação inicial (subtree)

- Unificação de repositórios (papers/notebooks/docs/projects) preservando histórico.

- CI (python + LaTeX) configurado.

- LFS reativado.

- DOI da release: 10.5281/zenodo.16921952

## v0.2.1 — 2025-08-25

- Metadados atualizados (CITATION.cff, metadata.yaml, zenodo.json).

- CI separado em testes Python e build LaTeX com artefatos.

- Workflow de release anexando PDFs e SBOM.

- Toolbox empacotada com pyproject e testes unitários.

- Badge de cobertura e ORCID no README.

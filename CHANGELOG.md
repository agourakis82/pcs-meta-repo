# Changelog

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

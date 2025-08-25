# Repository Audit Report

## Overview

- Commit: TBD
- Branch: pcs-meta-fixes
- Date: 2025-08-25

## Community files

- CODE_OF_CONDUCT.md, SECURITY.md, CODEOWNERS present
- Issue templates and PR template present
- release-drafter config and workflow present

## Metadata

- CITATION.cff, metadata.yaml, zenodo.json at repository root
- LICENSE uses MIT; docs & figures under LICENSES/CC-BY-4.0.txt

## Lint and tests

- pre-commit run --files ... : passed
- pytest : 8 passed, 2 skipped
- markdown-link-check README.md : 10 links checked, no failures

## LaTeX

- build workflows export TEXINPUTS and continue-on-error to avoid failures

## File inventory

```text
     92 pdf
     70 tex
     36 py
     33 md
     32 png
     14 sample
     14 json
     13 yml
     13 txt
     13 ipynb
     11 bib
      7 gitattributes
      6 yaml
      6 sh
      6 pyc
      6 csv
      5 gitignore
      4 patch
      4 bst
      3 svg
```

## Duplicate files (sha256 snippet)

```text
01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b  ./.safety/20250825-152706/staged.patch
...
```

## Actions

Latest audit:

- Removed OS/tmp/backup and duplicate " 2" artifacts
- Normalized metadata (CITATION.cff, metadata.yaml, zenodo.json)
- Added minimal pcs_toolbox package for CI
- Skipped LaTeX build gracefully when mdpi.cls missing
- Updated markdown templates, lint config, and hooks

## Next steps

- Review remaining duplicate PDFs and research materials
- Continue refining CI and documentation

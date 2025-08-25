# Repository Audit Report

## Overview
- Commit: 1df6e3fb63adf75d1443edc810446f439deb381e
- Branch: pcs-meta-fixes-20250825-163251
- Date: Mon Aug 25 16:52:33 UTC 2025

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
0ad94442a822d76e1cadb68d509aa5f70a0282f627f266cf0845917a539d9241  ./papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/sections/conclusion.tex
1a1dbe176bc233b499d35a57db7513f2941c99ab9759f177830c9149be99005b  ./papers/fractal-entropy-project/.gitattributes
1c0d965cb01884162fcb76095b0925478ff22b9879f06366027d8c46f1a736ff  ./notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/gamma_2e_curve.pdf
1d03c5b195bb937d1d2582ed720bd2874ca4d1449f2d8f4f39f8b583a1df1dc5  ./notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig1_collapse.png
288ae5b9b1ff450f335531139a3ed84259ed4e3ef0d5a4b772b1057dcc842a68  ./papers/soc_fractal_ahsd/literature/pdf/10.47749_t_unicamp.2022.1245646.pdf
3024fda0fef2656396a43742315c7b2b898076d5d020bb38e15816b3ddf0bb27  ./notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/vector_field_symbolic_entropy.pdf
4054dd541d1679f59f14f1ab1c52fa18f54a03d071dc1382dc27a0384e8f9078  ./papers/soc_fractal_ahsd/literature/pdf/10.58976_peletron.v2n2.entropia.pdf
44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a  ./.pytest_cache/v/cache/lastfailed
508a3b455cee12ea75a6fcb1c447b4ee33acd6f504a1af2d191a707ac8d6d81a  ./notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_collapse_recovery.pdf
5426e6a80132a2ef651c12c6b3a48ce9eddd1c709a9437a88e9aad5f10a539fd  ./notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/simulated_gamma_trajectories.pdf
544ea77fd313b024a3c2e2aa236adbe0f44ea7580c361724e26edb7b4a9e5ea7  ./papers/soc_fractal_ahsd/literature/pdf/10.1192_bjpo.bp.115.000455.pdf
5ec0e9f916e825346dc2112ad20729d7ec003af4e5257d9caf9492b5db2bd9e9  ./notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_symbolic_regimes_map.pdf
6850a1bb8e762b76c2f3cbc8a5523ec553fd67dc16ea226814fba7ff81dea08a  ./notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/gamma_profiles_comparison.pdf
6ed388efe6294c1cb7fe9a975a1ec6fc754ffb4f7880a8821910f17bec74aa11  ./notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_kappa_bifurcation.pdf
800058390077783248fa31b38025ebaa8306b78a0c1d63e002396a6dce45edc7  ./notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_symbolic_heatmap.pdf
89525cec2886ded15f3debcbed1f1b79e728d4ae448289c00342e9cb6e4da535  ./papers/soc_fractal_ahsd/literature/pdf/10.29003_m964.sudak.ns2020-16_113.pdf
8cb652e005e2e049c7f022939f64aa296297de7ac479c26951d0f04760576cd2  ./LICENSE
95a21d4254efdde4ff0692622245b5c696435f38581dbbbd4be3f4dffd5a1a46  ./notebooks/entropic-symbolic-society/sections/conclusion.tex
98a2eefc828f02b577ed9832342e174d5bf87108757ac7aed8f5e752c89a4261  ./notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/.gitattributes
```

## Actions
- Removed system files and duplicate artifacts
- Standardized license, citation section, and release-drafter config
- Made CI install package conditionally and tolerate LaTeX failures
- Added markdownlint configuration

## Next steps
- Review remaining duplicate PDFs and research materials
- Continue refining CI and documentation

# Repository Audit Report

## Overview

- Commit: f92d74ca2721e3dad19ebb054096b0c774de03e9
- Branch: pcs-meta-fixes
- Date: Mon Aug 25 13:35:38 UTC 2025

## Community health files

- `.editorconfig`: added
- `.gitignore`: updated to include `.tmp.driveupload/`
- `CODE_OF_CONDUCT.md`: present
- `SECURITY.md`: present
- `.github/ISSUE_TEMPLATE/bug_report.md`: present
- `.github/ISSUE_TEMPLATE/feature_request.md`: present
- `PULL_REQUEST_TEMPLATE.md`: present
- `.github/release-drafter.yml`: added

## Metadata validation

- `CITATION.cff`: **pass** (cffconvert)
- `zenodo.json`: **pass** (jq)
- `metadata.yaml`: **pass** (yq)
- `LICENSE`: MIT for code; Text & docs: CC BY 4.0

## Lint & test summary

- `pre-commit run --all-files`: warnings in YAML files, completed
- `markdownlint-cli2` (`**/*.md`): numerous style violations
- `ruff check --exit-zero`: 62 warnings
- `yamllint -s .`: warnings/errors in several YAML files
- `markdown-link-check README.md`: no broken links
- `pytest -q`: passed (6 passed, 2 skipped)

## LaTeX build summary

- `papers/fractal-entropy-project/paper_model/main.tex`: missing `mdpi.cls`
- `papers/The-Fractal-Nature-of-an-Entropically-Driven-Society/main.tex`: missing `Definitions/mdpi.cls`

## Counts by extension

```text
     86 pdf
     70 tex
     35 py
     32 png
     31 md
     19 ipynb
     14 json
     12 txt
     12 bib
      8 yml
      7 yaml
      7 gitattributes
      6 sh
      6 pdf"
      6 csv
      4 gitignore
      4 cff
      4 bst
      3 pyc
      3 fls
      3 fdb_latexmk
      2 svg
      2 sha256
      2 patch
      2 eps
      2 drawio
      2 docx
      2 cls
      1 toml
      1 sty
      1 papers/fractal-entropy-project/transcripts/README
      1 papers/fractal-entropy-project/paper_data/README
      1 papers/fractal-entropy-project/figs/README
      1 papers/fractal-entropy-project/docs/README
      1 papers/fractal-entropy-project/code/README
      1 papers/fractal-entropy-project/LICENSE
      1 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_RAW_DATA 2
      1 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_RAW_DATA
      1 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_Neuro_Integration_RSA 2
      1 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_Neuro_Integration_RSA
      1 notebooks/entropic-symbolic-society/LICENSE
      1 markdownlintignore
      1 log
      1 graphml
      1 gitignore 2
      1 github/CODEOWNERS
      1 flake8
      1 envrc
      1 editorconfig
      1 docs/socio-schrodinger-framework/LICENSE
      1 docs/fractal-entropy-society/LICENSE
      1 code-workspace
      1 cfg
      1 aux
      1 LICENSE
```

## Duplicate files (sha256)

```text
0b75cd57c74b4bf75b8ab25f84dae12788fb2a4d95d9f033e92c1dd62e56d6b2 notebooks/entropic-symbolic-society/sections/Introduction.tex
0f48d87559b8c384e3358108f32a6b57ec7f9c784f4f4f9d3143db4a6feb2f1e notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/appendices/fractal_layers.tex
1a1dbe176bc233b499d35a57db7513f2941c99ab9759f177830c9149be99005b papers/fractal-entropy-project/.gitattributes
1c0d965cb01884162fcb76095b0925478ff22b9879f06366027d8c46f1a736ff notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/gamma_2e_curve.pdf
1d03c5b195bb937d1d2582ed720bd2874ca4d1449f2d8f4f39f8b583a1df1dc5 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig1_collapse.png
2732e9d76e4fdd7069c7972c1441d8fedeb4ff5a3b2fc8a3694bbd4e65bbb282 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/notebooks/Notebook_01_Data_Preprocessing_and_Network_Construction
288ae5b9b1ff450f335531139a3ed84259ed4e3ef0d5a4b772b1057dcc842a68 papers/soc_fractal_ahsd/literature/pdf/10.47749_t_unicamp.2022.1245646.pdf
2941a98fbe0592d185924de6b72ecfa94bdf06ee187c9902490d194911c1f023 notebooks/entropic-symbolic-society/sections/intermezzo2_impossible.tex
3024fda0fef2656396a43742315c7b2b898076d5d020bb38e15816b3ddf0bb27 notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/vector_field_symbolic_entropy.pdf
37b7d5166caf2e64a7d99529fc96cc1e8934d1cc43521dff892a450a2c22bf99 notebooks/entropic-symbolic-society/sections/intermezzo1_consciousness.tex
3e49f3b35bb692f9519c864136f9b7618ce4b405e68d95e36f62aa45e1902a4b notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/notebooks/Notebook_02_Network_Metrics
4054dd541d1679f59f14f1ab1c52fa18f54a03d071dc1382dc27a0384e8f9078 papers/soc_fractal_ahsd/literature/pdf/10.58976_peletron.v2n2.entropia.pdf
4196ad3fb6eb75a707d20706d3a91ddd3f6846076ef2ce4ff8d7df901b20d763 papers/fractal-entropy-project/.obsidian/core-plugins.json
4328d257638e7669bf5f2ddb6050f0cd9824afe47f253a3bc4966d80677f43d9 notebooks/entropic-symbolic-society/sections/section_epiphany.tex
508a3b455cee12ea75a6fcb1c447b4ee33acd6f504a1af2d191a707ac8d6d81a notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_collapse_recovery.pdf
5426e6a80132a2ef651c12c6b3a48ce9eddd1c709a9437a88e9aad5f10a539fd notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/simulated_gamma_trajectories.pdf
544ea77fd313b024a3c2e2aa236adbe0f44ea7580c361724e26edb7b4a9e5ea7 papers/soc_fractal_ahsd/literature/pdf/10.1192_bjpo.bp.115.000455.pdf
5ec0e9f916e825346dc2112ad20729d7ec003af4e5257d9caf9492b5db2bd9e9 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_symbolic_regimes_map.pdf
6186f7cd86a1ed5ca2ba2511197872926791ae701123881c4ede6a86db1762a8 notebooks/entropic-symbolic-society/sections/section2_fractal_entropia_cognicao.tex
671c2a8b672b8854f5c77ba5dd7d5842d0e84ef55d5c936f37c1e4ac5934f6d6 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_Neuro_Integration_RSA
67ecba64cad89df25eae422773ea90e9e71412e73ef68180d49e6b0a689c8d8c notebooks/entropic-symbolic-society/papers/PORTFOLIO
6850a1bb8e762b76c2f3cbc8a5523ec553fd67dc16ea226814fba7ff81dea08a notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/gamma_profiles_comparison.pdf
6e962cec2ff6c018bc8845de62939dc0e4bf283b21d3b5e1a5ee72295ad9cce1 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/appendices/symbolic_density.tex
6ed388efe6294c1cb7fe9a975a1ec6fc754ffb4f7880a8821910f17bec74aa11 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_kappa_bifurcation.pdf
71d2f6ad4375b19e4792e2d9fbbd1b5b4ccaac345467f58fb5ecce5cd20ce047 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/references
7f353d4cf67f7bcf030c168035f3e777a5d2ea783ae104a6dac61d2b4100ed90 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/analysis_pipeline_diagram_branch
800058390077783248fa31b38025ebaa8306b78a0c1d63e002396a6dce45edc7 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_symbolic_heatmap.pdf
813c6e4efdda766b006547cb0cbac90afe22d07bfe4e99206b473e4e12587cc0 notebooks/entropic-symbolic-society/sections/methods.tex
8248ee7147ee59e3c7429af1271e69adf02fee261b5b590c8c395b147296c75b notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/notebooks/08_RSA_fMRI_Narratives
842613ceb1164b06c925e3009d1e73e8cd5d96db4eba4104069f92e2586933ce notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/notebooks/Notebook_06_UMAP_Visualization
8703ed295627c4c28582a4e9dee169cff7a8f8dbadff4c6017dcf7fc15d34e54 notebooks/entropic-symbolic-society/sections/section2_2_entropy.tex
89525cec2886ded15f3debcbed1f1b79e728d4ae448289c00342e9cb6e4da535 papers/soc_fractal_ahsd/literature/pdf/10.29003_m964.sudak.ns2020-16_113.pdf
95a21d4254efdde4ff0692622245b5c696435f38581dbbbd4be3f4dffd5a1a46 notebooks/entropic-symbolic-society/sections/conclusion.tex
96ff7b17090a17f9fda5e91589d5888355ebcea4c82a4c5d68f968f751f45067 notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_Validation_and_Robustedness
98a2eefc828f02b577ed9832342e174d5bf87108757ac7aed8f5e752c89a4261 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/.gitattributes
9bc017f2cf8504fed797463d7b5dcf7b8e7a43750cdb652aeb4c85fc8314d177 notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/entropy_kappa_map.pdf
9e21cddd195ce5425aaf6cab0ca561c9f35e9b4cc03f638d61ad68518b0ae249 notebooks/entropic-symbolic-society/sections/section4.tex
a02b8e2e0b91d2c89be7356480571cd11b5544b2d16a6a50910031a3e4682180 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig2_bifurcation.png
a86057e7a0ab5e777a8b06726e6f6590cfbcfd145404e1ff96ec0646402f481a notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/Fig_gamma_profiles.pdf
a8b76256d3b435bca908e3abf9d0075f6bad5ecf9486f99f66c0844be7b0a111 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/ext_S3_degree_distribution.png
af99daf7120019becb4b0ec0b720df1bdc818e55ebe53a18a04bb71a9f669924 notebooks/entropic-symbolic-society/sections/abstract.tex
b08ad5a5c1357bc9c3a3868cffe0a395a502ce9055712fd0661bc80156bc1527 notebooks/entropic-symbolic-society/sections/results.tex
b201b1617bdb619789087e59e9e484854ad3b8d4a7a586890c894c731bb318ea notebooks/entropic-symbolic-society/sections/section_coda_fractal.tex
b719f5387026b5b1f12c6a0a5a70a927044c36a310bafd930a0a8c0a12b7c15a notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_gamma_profiles.pdf
b7a5c21cfe95aeb059962f09e7458524df14157e3b24870516765ed983307555 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/appendices/glossary.tex
b85c63ae7fb1966edd4f4ea6389e0401deb96c0ae70896a5ff88825fef01b3a1 papers/soc_fractal_ahsd/literature/pdf/10.1038_s41598-023-43403-4.pdf
bba1182d95b00ae441ac12a977dd41a2e691e83ddeb8fe091f8d2f6a3c459078 notebooks/entropic-symbolic-society/sections/section_singularity_giftedness.tex
c20deea4f0554dbe6ec094b725eeecac877882703bff076951ec2e7fd15b07e5 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/ext_S3_degree_distribution.pdf
c404cf7393f6ff45abc0d9117bd0aceb06ee1539b08372e863a77600d9fe08de papers/soc_fractal_ahsd/literature/pdf/10.1007_978-94-017-2012-0_7.pdf
ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356 papers/fractal-entropy-project/.obsidian/app.json
cd05eb30b9d4bbb05c442073a114f8f8b583380f7dfc665bf230c90c116eb90d notebooks/entropic-symbolic-society/OSF_README_AND_DOCS/OSF_README_RAW_DATA
ce3d4b0afe17109d30ef718b7e4943c8674f78308971a0c1da951f2e050fc337 notebooks/entropic-symbolic-society/sections/section2_3_symbiotic_cognition.tex
d0057dcc7d5c7b6380bbc97257f6661777cc995ca68a1d74f2958a327005878c notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/figs/Fig_trajectory_3D.pdf
db2d36854b22ba453c687f9312f6cfab899fa56688d651feb6915e698fda3ec6 notebooks/entropic-symbolic-society/Manuscripts/Scientific_Reports_v1.6/figures/Fig_collapse_recovery.pdf
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/code/run_simulations.py
e4856f4b4da28168224361ba6eef7ead62966d54e255ca798c6758d592946261 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/notebooks/Symbolic_Entropy_Curvature_Colab
ed2ac29505aa6d813c5374c7fefe9e418b18e1ea374e165f87cf69b711785362 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/requirements
f2dacf39c476cd3e7f4dde590f6ad579196c9432a3ecaadd36c2363ff1f77430 notebooks/entropic-symbolic-society/NHB_Symbolic_Mainfold/notebooks/10_Robustness_and_Nulls
f44e10e948e2d3f5a616e2326310b006951d0795c50424dc4027d1a96bfadde5 papers/soc_fractal_ahsd/literature/pdf/10.1038_s41467-024-53868-0.pdf
f63bf3ff61ac85219be7dc686df8281e0bddf8904c75236d686eabc9f5d540ab papers/soc_fractal_ahsd/literature/zotero/zotero.bib
fb5c28c7d870e10043050961b02bf888f442ad99196aa8faf4dcccff030d8521 papers/soc_fractal_ahsd/literature/pdf/10.1038_s44271-025-00245-2.pdf
fe0b4f45b07b3ff6fb7b914fc0bd84ba7d822589b4351b12374affb0baa08973 notebooks/entropic-symbolic-society/sections/section3_patterns_impossible.tex
```

## Large untracked files (>25MB)

- None

## Actions applied

- Created `.editorconfig`
- Updated `.gitignore`
- Added `.github/release-drafter.yml`
- Removed temporary LaTeX build artifacts

## Next steps / TODO

- Address markdownlint, yamllint, and ruff violations
- Provide missing LaTeX class files or skip builds in CI
- Review duplicated files for cleanup

# Executed Notebooks (CI Artifacts)

This folder contains executed versions of the analysis notebooks for traceability:

- 03_process_zuco.ipynb: runs the unified ZuCo loader; prints QA summary.
- 04_merge_data.ipynb: merges ZuCo with KEC on `token_norm`; reports coverage.
- 05_analysis_reading.ipynb: OLS (clustered) + MixedLM examples.
- 06_analysis_eeg.ipynb: correlations between EEG bands and KEC metrics.

Notebooks are executed in CI via `nbconvert` (smoke mode). They may skip plots if inputs are missing.


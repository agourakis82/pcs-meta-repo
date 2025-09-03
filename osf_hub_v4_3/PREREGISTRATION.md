Title. Symbolic-First validation (SWOW→KEC→ZuCo).
Datasets. SWOW (public); ZuCo 1.0/2.0 (ET+EEG; public). No PII.
H1. Higher KEC predicts increased sentence-level reading cost.
H2. KEC correlates with fixation-locked θ/α EEG features.
Outcomes. Primary: sentence-level reading cost; Secondary: fixation-locked θ/α.
Model. OLS (HC-robust SEs); MixedLM (random intercepts = sentence/subject).
Multiple testing. BH-FDR across families; report q-values.
Placebos. Degree-preserving null graphs (N≥1000).
Exclusion. Standard ZuCo artefact criteria (preregister thresholds if used).
Bootstrap. 2,000 reps for CIs. Seeds. Pinned in `provenance.yaml`.
Reporting. `*_coeffs.csv`, `*_fdr.csv`, `mixedlm_*_summary.txt` + F2/F3.
Deviations. Log in CHANGELOG + OSF Registration update.

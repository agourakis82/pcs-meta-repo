# ZuCo Loader & ET+EEG Alignment (v1+v2)
**Goal:** produce a single token-level table from ZuCo v1 & v2 with Eye-Tracking (FFD, GD, TRT, GPT) and EEG band power (theta1, alpha1, beta1, gamma1), keyed by (Dataset, Task, Subject, SentenceID, w_pos, token_norm).

## Alignment rules
- Build `token_norm` = lowercase, accent/punctuation stripped.
- For each sentence, match EEG segments only to **fixated** tokens; skipped tokens keep ET=0, EEG=NaN.
- If a token has multiple EEG segments (refixations/regressions), average band power **per token**.
- Merge ET and EEG on (Dataset, Task, Subject, SentenceID, w_pos, token_norm).
- Export:
  - `data/processed/zuco_aligned.csv`
  - `reports/zuco_loader_qa.json` (coverage, skips, env, anomalies)



### 2025-09-11 21:01:30 — integrate

Métodos utilizados:
- KEC merge: canonical columns [word, entropy, curvature, coherence], with components prefixed as comp_* and deduplicated per word.
- RT join: per-language join_key; en uses first alphabetical sequence (>=2 chars); others use lowercase word.
- OneStop ET: auto-select text column (word/token/word_form/orth) if 'word' is mostly bracket markers; drop empty tokens after normalization.
- KEC dedup by join_key before merge to avoid row explosion; RT outputs also saved with _kec_rt alias for coverage.

Artefatos gerados:
- data/processed/v4.4/integration/derco_kec_eeg.parquet
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/lpp_kec_eeg.parquet
- data/processed/v4.4/integration/onestop_et.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_eeg.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de cobertura (top 10):
- zuco_kec_rt.parquet entropy: 485/800 (60.6%)
- zuco_kec_rt.parquet curvature: 485/800 (60.6%)
- zuco_kec_rt.parquet coherence: 550/800 (68.8%)
- excel_custom_kec_rt.parquet entropy: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet curvature: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet coherence: 747972/1083443 (69.0%)
- geco_et_kec_rt.parquet entropy: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet curvature: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet coherence: 237480/827966 (28.7%)
- onestop_et_kec_rt.parquet entropy: 56246/62675 (89.7%)

### 2025-09-11 21:07:18 — integrate

Métodos utilizados:
- KEC merge: canonical columns [word, entropy, curvature, coherence], with components prefixed as comp_* and deduplicated per word.
- RT join: per-language join_key; en uses first alphabetical sequence (>=2 chars); others use lowercase word.
- OneStop ET: auto-select text column (word/token/word_form/orth) if 'word' is mostly bracket markers; drop empty tokens after normalization.
- KEC dedup by join_key before merge to avoid row explosion; RT outputs also saved with _kec_rt alias for coverage.

Artefatos gerados:
- data/processed/v4.4/integration/derco_kec_eeg.parquet
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/lpp_kec_eeg.parquet
- data/processed/v4.4/integration/onestop_et.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_eeg.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de cobertura (top 10):
- zuco_kec_rt.parquet entropy: 485/800 (60.6%)
- zuco_kec_rt.parquet curvature: 485/800 (60.6%)
- zuco_kec_rt.parquet coherence: 550/800 (68.8%)
- excel_custom_kec_rt.parquet entropy: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet curvature: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet coherence: 747972/1083443 (69.0%)
- geco_et_kec_rt.parquet entropy: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet curvature: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet coherence: 237480/827966 (28.7%)
- onestop_et_kec_rt.parquet entropy: 56246/62675 (89.7%)

### 2025-09-11 21:17:47 — integrate

Métodos utilizados:
- KEC merge: canonical columns [word, entropy, curvature, coherence], with components prefixed as comp_* and deduplicated per word.
- RT join: per-language join_key; en uses first alphabetical sequence (>=2 chars); others use lowercase word.
- OneStop ET: auto-select text column (word/token/word_form/orth) if 'word' is mostly bracket markers; drop empty tokens after normalization.
- KEC dedup by join_key before merge to avoid row explosion; RT outputs also saved with _kec_rt alias for coverage.

Artefatos gerados:
- data/processed/v4.4/integration/derco_kec_eeg.parquet
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/lpp_kec_eeg.parquet
- data/processed/v4.4/integration/onestop_et.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_eeg.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de cobertura (top 10):
- zuco_kec_rt.parquet entropy: 485/800 (60.6%)
- zuco_kec_rt.parquet curvature: 485/800 (60.6%)
- zuco_kec_rt.parquet coherence: 550/800 (68.8%)
- excel_custom_kec_rt.parquet entropy: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet curvature: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet coherence: 747972/1083443 (69.0%)
- geco_et_kec_rt.parquet entropy: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet curvature: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet coherence: 237480/827966 (28.7%)
- onestop_et_kec_rt.parquet entropy: 56246/62675 (89.7%)

### 2025-09-11 21:31:46 — models_rt

Métodos utilizados:
- Per-dataset Spearman rank correlation between RT/ET measures and KEC metrics (entropy, curvature, coherence).
- Multiple DVs auto-detected via column name heuristics (rt, gaze, fix, duration, trt).
- P-values approximated from correlation t-stat; BH-FDR correction across all tests per run.
- Controls not included in correlation; advise using mixed models separately if needed.

Artefatos gerados:
- reports/v4.4/models_rt_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_rt.parquet trt_ms~entropy: r=0.038, p=0.4671092445903873, q=0.0 (n=367)
- zuco_kec_rt.parquet trt_ms~curvature: r=0.002, p=0.9741095222037928, q=0.0 (n=367)
- zuco_kec_rt.parquet trt_ms~coherence: r=-0.036, p=0.45403935089433656, q=0.0 (n=428)
- zuco_kec_rt.parquet nfix~entropy: r=0.045, p=0.3849365625636607, q=0.0 (n=367)
- zuco_kec_rt.parquet nfix~curvature: r=0.022, p=0.667984052787576, q=0.0 (n=367)
- zuco_kec_rt.parquet nfix~coherence: r=-0.039, p=0.4240225574438914, q=0.0 (n=428)
- geco_et_kec_rt.parquet timestamp~entropy: r=-0.052, p=0.0, q=0.0 (n=129159)
- geco_et_kec_rt.parquet timestamp~curvature: r=-0.108, p=0.0, q=0.0 (n=129159)
- geco_et_kec_rt.parquet timestamp~coherence: r=-0.337, p=0.0, q=0.0 (n=237480)

### 2025-09-11 21:31:46 — models_eeg

Métodos utilizados:
- Per-dataset Spearman rank correlation between EEG band power and KEC metrics (entropy, curvature, coherence).
- EEG DVs auto-detected via columns starting with 'eeg_' or containing theta/alpha/beta/gamma.
- P-values approximated from correlation t-stat; BH-FDR correction across all tests per run.

Artefatos gerados:
- reports/v4.4/models_eeg_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_eeg.parquet eeg_alpha~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_alpha~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_alpha~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_theta~entropy: r=nan, p=nan, q=None (n=0)

### 2025-09-11 21:35:13 — integrate

Métodos utilizados:
- KEC merge: canonical columns [word, entropy, curvature, coherence], with components prefixed as comp_* and deduplicated per word.
- RT join: per-language join_key; en uses first alphabetical sequence (>=2 chars); others use lowercase word.
- OneStop ET: auto-select text column (word/token/word_form/orth) if 'word' is mostly bracket markers; drop empty tokens after normalization.
- KEC dedup by join_key before merge to avoid row explosion; RT outputs also saved with _kec_rt alias for coverage.

Artefatos gerados:
- data/processed/v4.4/integration/derco_kec_eeg.parquet
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/lpp_kec_eeg.parquet
- data/processed/v4.4/integration/onestop_et.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_eeg.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de cobertura (top 10):
- zuco_kec_rt.parquet entropy: 485/800 (60.6%)
- zuco_kec_rt.parquet curvature: 485/800 (60.6%)
- zuco_kec_rt.parquet coherence: 550/800 (68.8%)
- excel_custom_kec_rt.parquet entropy: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet curvature: 671579/1083443 (62.0%)
- excel_custom_kec_rt.parquet coherence: 747972/1083443 (69.0%)
- geco_et_kec_rt.parquet entropy: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet curvature: 129159/827966 (15.6%)
- geco_et_kec_rt.parquet coherence: 237480/827966 (28.7%)
- onestop_et_kec_rt.parquet entropy: 56246/62675 (89.7%)

### 2025-09-11 21:36:40 — models_rt

Métodos utilizados:
- Per-dataset Spearman rank correlation between RT/ET measures and KEC metrics (entropy, curvature, coherence).
- Multiple DVs auto-detected via column name heuristics (rt, gaze, fix, duration, trt).
- P-values approximated from correlation t-stat; BH-FDR correction across all tests per run.
- Controls not included in correlation; advise using mixed models separately if needed.

Artefatos gerados:
- reports/v4.4/models_rt_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_rt.parquet trt_ms~entropy: r=0.038, p=0.4671092445903873, q=3e-300 (n=367)
- zuco_kec_rt.parquet trt_ms~curvature: r=0.002, p=0.9741095222037928, q=3e-300 (n=367)
- zuco_kec_rt.parquet trt_ms~coherence: r=-0.036, p=0.45403935089433656, q=3e-300 (n=428)
- zuco_kec_rt.parquet nfix~entropy: r=0.045, p=0.3849365625636607, q=3e-300 (n=367)
- zuco_kec_rt.parquet nfix~curvature: r=0.022, p=0.667984052787576, q=3e-300 (n=367)
- zuco_kec_rt.parquet nfix~coherence: r=-0.039, p=0.4240225574438914, q=3e-300 (n=428)
- geco_et_kec_rt.parquet timestamp~entropy: r=-0.052, p=0.0, q=9e-300 (n=129159)
- geco_et_kec_rt.parquet timestamp~curvature: r=-0.108, p=0.0, q=4.5e-300 (n=129159)
- geco_et_kec_rt.parquet timestamp~coherence: r=-0.337, p=0.0, q=3e-300 (n=237480)

### 2025-09-11 21:36:41 — models_eeg

Métodos utilizados:
- Per-dataset Spearman rank correlation between EEG band power and KEC metrics (entropy, curvature, coherence).
- EEG DVs auto-detected via columns starting with 'eeg_' or containing theta/alpha/beta/gamma.
- P-values approximated from correlation t-stat; BH-FDR correction across all tests per run.

Artefatos gerados:
- reports/v4.4/models_eeg_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_eeg.parquet eeg_alpha~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_alpha~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_alpha~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_theta~entropy: r=nan, p=nan, q=None (n=0)

### 2025-09-11 21:45:40 — models_rt

Métodos utilizados:
- Per-dataset Spearman rank correlation (SciPy exact when available) between RT/ET measures and KEC metrics (entropy, curvature, coherence).
- Multiple DVs auto-detected via column name heuristics (rt, gaze, fix, duration, trt).
- BH-FDR correction applied per dataset/file family.
- Controls not included in correlation; advise using mixed models separately if needed.

Artefatos gerados:
- reports/v4.4/models_rt_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_rt.parquet trt_ms~entropy: r=0.038, p=0.46757539552270355, q=0.7013630932840553 (n=367)
- zuco_kec_rt.parquet trt_ms~curvature: r=0.002, p=0.974127261752011, q=0.7013630932840553 (n=367)
- zuco_kec_rt.parquet trt_ms~coherence: r=-0.036, p=0.4544525211558629, q=0.9089050423117259 (n=428)
- zuco_kec_rt.parquet nfix~entropy: r=0.045, p=0.3855074948101562, q=1.0 (n=367)
- zuco_kec_rt.parquet nfix~curvature: r=0.022, p=0.668237086356122, q=0.7013630932840553 (n=367)
- zuco_kec_rt.parquet nfix~coherence: r=-0.039, p=0.4244680928683463, q=1.0 (n=428)
- geco_et_kec_rt.parquet timestamp~entropy: r=-0.052, p=2.6175197682254076e-77, q=1.5e-300 (n=129159)
- geco_et_kec_rt.parquet timestamp~curvature: r=-0.108, p=0.0, q=3e-300 (n=129159)
- geco_et_kec_rt.parquet timestamp~coherence: r=-0.337, p=0.0, q=1.5e-300 (n=237480)

### 2025-09-11 21:45:40 — models_eeg

Métodos utilizados:
- Per-dataset Spearman rank correlation (SciPy exact when available) between EEG band power and KEC metrics (entropy, curvature, coherence).
- EEG DVs auto-detected via columns starting with 'eeg_' or containing theta/alpha/beta/gamma.
- BH-FDR correction applied per dataset/file family.

Artefatos gerados:
- reports/v4.4/models_eeg_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_eeg.parquet eeg_alpha~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_alpha~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_alpha~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_beta~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~entropy: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~curvature: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_gamma~coherence: r=nan, p=nan, q=None (n=0)
- zuco_kec_eeg.parquet eeg_theta~entropy: r=nan, p=nan, q=None (n=0)

### 2025-09-11 22:22:03 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

### 2025-09-11 22:52:15 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 367, 'coef_metric': -8.034035619707998, 'coef': -8.034035619707998, '|coef|': 8.034035619707998, 'se_metric': 178.26215665481712, 'z_approx': -0.04506865489833003, 'p': 0.9640525857922448, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 367, 'coef_metric': 411.42468790701724, 'coef': 411.42468790701724, '|coef|': 411.42468790701724, 'se_metric': 8644.478489256217, 'z_approx': 0.04759392812630121, 'p': 0.9620398712008287, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 428, 'coef_metric': -4.17972326684735, 'coef': -4.17972326684735, '|coef|': 4.17972326684735, 'se_metric': 607.9419241397023, 'z_approx': -0.006875201562652665, 'p': 0.9945144260365, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 0.9945144260365}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 367, 'coef_metric': 0.03984649951275071, 'coef': 0.03984649951275071, '|coef|': 0.03984649951275071, 'se_metric': 1.2421073982268525, 'z_approx': 0.03207975378750086, 'p': 0.9744084492365688, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 367, 'coef_metric': -0.14616897818096758, 'coef': -0.14616897818096758, '|coef|': 0.14616897818096758, 'se_metric': 60.23370090771453, 'z_approx': -0.0024266976124365414, 'p': 0.9980637773416576, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.9980637773416575, 'q_fdr_by_dv': 0.9980637773416575}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 428, 'coef_metric': 0.15481143692152094, 'coef': 0.15481143692152094, '|coef|': 0.15481143692152094, 'se_metric': 4.18576305514912, 'z_approx': 0.03698523659409711, 'p': 0.9704967771782955, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}

### 2025-09-12 06:12:24 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 367, 'coef_metric': -8.034035619707998, 'coef': -8.034035619707998, '|coef|': 8.034035619707998, 'se_metric': 178.26215665481712, 'z_approx': -0.04506865489833003, 'p': 0.9640525857922448, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 367, 'coef_metric': 411.42468790701724, 'coef': 411.42468790701724, '|coef|': 411.42468790701724, 'se_metric': 8644.478489256217, 'z_approx': 0.04759392812630121, 'p': 0.9620398712008287, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 428, 'coef_metric': -4.17972326684735, 'coef': -4.17972326684735, '|coef|': 4.17972326684735, 'se_metric': 607.9419241397023, 'z_approx': -0.006875201562652665, 'p': 0.9945144260365, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 0.9945144260365}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 367, 'coef_metric': 0.03984649951275071, 'coef': 0.03984649951275071, '|coef|': 0.03984649951275071, 'se_metric': 1.2421073982268525, 'z_approx': 0.03207975378750086, 'p': 0.9744084492365688, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 367, 'coef_metric': -0.14616897818096758, 'coef': -0.14616897818096758, '|coef|': 0.14616897818096758, 'se_metric': 60.23370090771453, 'z_approx': -0.0024266976124365414, 'p': 0.9980637773416576, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.9980637773416575, 'q_fdr_by_dv': 0.9980637773416575}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 428, 'coef_metric': 0.15481143692152094, 'coef': 0.15481143692152094, '|coef|': 0.15481143692152094, 'se_metric': 4.18576305514912, 'z_approx': 0.03698523659409711, 'p': 0.9704967771782955, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}

### 2025-09-12 06:29:33 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 367, 'coef_metric': -8.034026978796051, 'coef': -8.034026978796051, '|coef|': 8.034026978796051, 'se_metric': 178.2621628007182, 'z_approx': -0.04506860487145219, 'p': 0.9640526256674007, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 367, 'coef_metric': 411.42428039222483, 'coef': 411.42428039222483, '|coef|': 411.42428039222483, 'se_metric': 8644.478373065082, 'z_approx': 0.047593881624386054, 'p': 0.9620399082619899, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 428, 'coef_metric': -4.1797231673243544, 'coef': -4.1797231673243544, '|coef|': 4.1797231673243544, 'se_metric': 607.941925750068, 'z_approx': -0.006875201380736303, 'p': 0.9945144261816448, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 0.9945144261816448}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 367, 'coef_metric': 0.039846552732851, 'coef': 0.039846552732851, '|coef|': 0.039846552732851, 'se_metric': 1.2421074410383157, 'z_approx': 0.03207979552843033, 'p': 0.9744084159492583, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 367, 'coef_metric': -0.14617161903148096, 'coef': -0.14617161903148096, '|coef|': 0.14617161903148096, 'se_metric': 60.23370009772313, 'z_approx': -0.0024267414884745946, 'p': 0.9980637423337475, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.9980637423337475, 'q_fdr_by_dv': 0.9980637423337475}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 428, 'coef_metric': 0.15481143637065534, 'coef': 0.15481143637065534, '|coef|': 0.15481143637065534, 'se_metric': 4.185763066236778, 'z_approx': 0.03698523636452242, 'p': 0.9704967773613444, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}

### 2025-09-12 06:31:45 — integrate

Métodos utilizados:
- KEC merge: canonical columns [word, entropy, curvature, coherence], with components prefixed as comp_* and deduplicated per word.
- RT join: per-language join_key; en uses first alphabetical sequence (>=2 chars); others use lowercase word.
- OneStop ET: auto-select text column (word/token/word_form/orth) if 'word' is mostly bracket markers; drop empty tokens after normalization.
- KEC dedup by join_key before merge to avoid row explosion; RT outputs also saved with _kec_rt alias for coverage.

Artefatos gerados:
- data/processed/v4.4/integration/derco_kec_eeg.parquet
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/lpp_kec_eeg.parquet
- data/processed/v4.4/integration/onestop_et.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_eeg.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de cobertura (top 10):
- zuco_kec_rt.parquet entropy: 545/800 (68.1%)
- zuco_kec_rt.parquet curvature: 545/800 (68.1%)
- zuco_kec_rt.parquet coherence: 675/800 (84.4%)
- excel_custom_kec_rt.parquet entropy: 797051/1083443 (73.6%)
- excel_custom_kec_rt.parquet curvature: 797051/1083443 (73.6%)
- excel_custom_kec_rt.parquet coherence: 947804/1083443 (87.5%)
- geco_et_kec_rt.parquet entropy: 144062/827966 (17.4%)
- geco_et_kec_rt.parquet curvature: 144062/827966 (17.4%)
- geco_et_kec_rt.parquet coherence: 348333/827966 (42.1%)
- onestop_et_kec_rt.parquet entropy: 56246/62675 (89.7%)

### 2025-09-12 06:33:32 — models_rt

Métodos utilizados:
- Per-dataset Spearman rank correlation (SciPy exact when available) between RT/ET measures and KEC metrics (entropy, curvature, coherence).
- Multiple DVs auto-detected via column name heuristics (rt, gaze, fix, duration, trt).
- BH-FDR correction applied per dataset/file family.
- Controls not included in correlation; advise using mixed models separately if needed.

Artefatos gerados:
- reports/v4.4/models_rt_summary_v4.4.csv

Snapshot de resultados (top 10):
- zuco_kec_rt.parquet trt_ms~entropy: r=0.023, p=0.6361361704888533, q=1.0 (n=415)
- zuco_kec_rt.parquet trt_ms~curvature: r=-0.021, p=0.6716279530766704, q=1.0 (n=415)
- zuco_kec_rt.parquet trt_ms~coherence: r=-0.028, p=0.5259362949120399, q=1.0 (n=509)
- zuco_kec_rt.parquet nfix~entropy: r=0.031, p=0.5295284259184319, q=1.0 (n=415)
- zuco_kec_rt.parquet nfix~curvature: r=-0.010, p=0.8329294044886365, q=0.8329294044886365 (n=415)
- zuco_kec_rt.parquet nfix~coherence: r=-0.012, p=0.7919985879334113, q=0.9503983055200935 (n=509)
- geco_et_kec_rt.parquet timestamp~entropy: r=-0.058, p=2.1997434341757544e-107, q=3e-300 (n=144062)
- geco_et_kec_rt.parquet timestamp~curvature: r=-0.082, p=2.906185081015226e-212, q=3e-300 (n=144062)
- geco_et_kec_rt.parquet timestamp~coherence: r=-0.270, p=0.0, q=3e-300 (n=348333)

### 2025-09-12 06:39:09 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': -3.3602409135596183, 'coef': -3.3602409135596183, '|coef|': 3.3602409135596183, 'se_metric': 163.70719944905522, 'z_approx': -0.020525920209179968, 'p': 0.9836238350931847, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.9836238350931849, 'q_fdr_by_dv': 0.9836238350931849}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -577.3908270439964, 'coef': -577.3908270439964, '|coef|': 577.3908270439964, 'se_metric': 7919.180820220959, 'z_approx': -0.07291042345815336, 'p': 0.9418773993019267, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -56.998543155366924, 'coef': -56.998543155366924, '|coef|': 56.998543155366924, 'se_metric': 69.5066635274293, 'z_approx': -0.8200442988156623, 'p': 0.4121908540840933, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': -0.0035413878973579852, 'coef': -0.0035413878973579852, '|coef|': 0.0035413878973579852, 'se_metric': 0.14209556767548812, 'z_approx': -0.024922578200649144, 'p': 0.9801167180263457, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 0.9801167180263457}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -4.508463939385374, 'coef': -4.508463939385374, '|coef|': 4.508463939385374, 'se_metric': 54.44728593288531, 'z_approx': -0.08280419973445054, 'p': 0.9340072296933641, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -0.06912934809203362, 'coef': -0.06912934809203362, '|coef|': 0.06912934809203362, 'se_metric': 0.49482701761530656, 'z_approx': -0.1397040695659364, 'p': 0.8888938108946487, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}

### 2025-09-12 06:48:52 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'geco_et_kec_rt.parquet', 'dataset': 'geco_et', 'dv': 'gaze_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 51629, 'coef_metric': -2.3646862246096145e-10, 'coef': -2.3646862246096145e-10, '|coef|': 2.3646862246096145e-10, 'se_metric': 1.1422834460748828e-12, 'z_approx': -207.01396249198524, 'p': 0.0, 'converged': True, 'controls': 'length,freq_local', 'random_effects': 'meta(DL) over subjects k=2, tau2=0', 'method': 'meta_subjects', 'q_fdr': 3e-300, 'q_fdr_by_dv': 3e-300}
- {'file': 'geco_et_kec_rt.parquet', 'dataset': 'geco_et', 'dv': 'gaze_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 51629, 'coef_metric': -1.3737007975578282e-08, 'coef': -1.3737007975578282e-08, '|coef|': 1.3737007975578282e-08, 'se_metric': 7.081112796659042e-11, 'z_approx': -193.99504527112708, 'p': 0.0, 'converged': True, 'controls': 'length,freq_local', 'random_effects': 'meta(DL) over subjects k=2, tau2=0', 'method': 'meta_subjects', 'q_fdr': 1.5e-300, 'q_fdr_by_dv': 1.5e-300}
- {'file': 'geco_et_kec_rt.parquet', 'dataset': 'geco_et', 'dv': 'gaze_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 71951, 'coef_metric': -6.139183554000375, 'coef': -6.139183554000375, '|coef|': 6.139183554000375, 'se_metric': 1000000.0, 'z_approx': -6.139183554000375e-06, 'p': 0.9999951016402264, 'converged': True, 'controls': 'length,freq_local', 'random_effects': 'meta(DL) over subjects k=2, tau2=2.184e+12', 'method': 'meta_subjects', 'q_fdr': 1.5e-300, 'q_fdr_by_dv': 1.5e-300}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': -3.3602409135596183, 'coef': -3.3602409135596183, '|coef|': 3.3602409135596183, 'se_metric': 163.70719944905522, 'z_approx': -0.020525920209179968, 'p': 0.9836238350931847, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.9836238350931849, 'q_fdr_by_dv': 0.9836238350931849}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -577.3908270439964, 'coef': -577.3908270439964, '|coef|': 577.3908270439964, 'se_metric': 7919.180820220959, 'z_approx': -0.07291042345815336, 'p': 0.9418773993019267, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -56.998543155366924, 'coef': -56.998543155366924, '|coef|': 56.998543155366924, 'se_metric': 69.5066635274293, 'z_approx': -0.8200442988156623, 'p': 0.4121908540840933, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': -0.0035413878973579852, 'coef': -0.0035413878973579852, '|coef|': 0.0035413878973579852, 'se_metric': 0.14209556767548812, 'z_approx': -0.024922578200649144, 'p': 0.9801167180263457, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 0.9801167180263457}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -4.508463939385374, 'coef': -4.508463939385374, '|coef|': 4.508463939385374, 'se_metric': 54.44728593288531, 'z_approx': -0.08280419973445054, 'p': 0.9340072296933641, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -0.06912934809203362, 'coef': -0.06912934809203362, '|coef|': 0.06912934809203362, 'se_metric': 0.49482701761530656, 'z_approx': -0.1397040695659364, 'p': 0.8888938108946487, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}

### 2025-09-12 07:09:36 — surprisal

Métodos utilizados:
- KenLM per-token surprisal when available; unigram proxy otherwise
- Sentence-conditioned using stateful scoring; bits as units

Artefatos gerados:
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet'}
- {'file': 'excel_custom_kec_rt.parquet'}
- {'file': 'geco_et_kec_rt.parquet'}
- {'file': 'onestop_et_kec_rt.parquet'}

### 2025-09-12 07:10:40 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': -3.3602409135596183, 'coef': -3.3602409135596183, '|coef|': 3.3602409135596183, 'se_metric': 163.70719944905522, 'z_approx': -0.020525920209179968, 'p': 0.9836238350931847, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.9836238350931849, 'q_fdr_by_dv': 0.9836238350931849}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -577.3908270439964, 'coef': -577.3908270439964, '|coef|': 577.3908270439964, 'se_metric': 7919.180820220959, 'z_approx': -0.07291042345815336, 'p': 0.9418773993019267, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -56.998543155366924, 'coef': -56.998543155366924, '|coef|': 56.998543155366924, 'se_metric': 69.5066635274293, 'z_approx': -0.8200442988156623, 'p': 0.4121908540840933, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': -0.0035413878973579852, 'coef': -0.0035413878973579852, '|coef|': 0.0035413878973579852, 'se_metric': 0.14209556767548812, 'z_approx': -0.024922578200649144, 'p': 0.9801167180263457, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 0.9801167180263457}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -4.508463939385374, 'coef': -4.508463939385374, '|coef|': 4.508463939385374, 'se_metric': 54.44728593288531, 'z_approx': -0.08280419973445054, 'p': 0.9340072296933641, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -0.06912934809203362, 'coef': -0.06912934809203362, '|coef|': 0.06912934809203362, 'se_metric': 0.49482701761530656, 'z_approx': -0.1397040695659364, 'p': 0.8888938108946487, 'converged': True, 'controls': 'length,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 1.0, 'q_fdr_by_dv': 1.0}

### 2025-09-12 07:23:46 — surprisal

Métodos utilizados:
- KenLM per-token surprisal when available; transformer surprisal when TRF_SURPRISAL=1; unigram proxy otherwise
- KenLM: sentence-conditioned stateful scoring; Transformer: per-sentence forward with token logprobs aggregated to words; bits as units

Artefatos gerados:
- data/processed/v4.4/integration/excel_custom_kec_rt.parquet
- data/processed/v4.4/integration/geco_et_kec_rt.parquet
- data/processed/v4.4/integration/onestop_et_kec_rt.parquet
- data/processed/v4.4/integration/zuco_kec_rt.parquet

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet'}
- {'file': 'excel_custom_kec_rt.parquet'}
- {'file': 'geco_et_kec_rt.parquet'}
- {'file': 'onestop_et_kec_rt.parquet'}

### 2025-09-12 07:24:48 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency + surprisal?; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency), plus surprisal (surprisal_trf if available else surprisal).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': 2.0427669740387286, 'coef': 2.0427669740387286, '|coef|': 2.0427669740387286, 'se_metric': 20.447589604596043, 'z_approx': 0.09990258086848398, 'p': 0.9204216673674048, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.33154871931409646}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -1691.9240061847902, 'coef': -1691.9240061847902, '|coef|': 1691.9240061847902, 'se_metric': 1060.1844138684487, 'z_approx': -1.5958770795462098, 'p': 0.11051623977136549, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.33154871931409646}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -49.33960565972466, 'coef': -49.33960565972466, '|coef|': 49.33960565972466, 'se_metric': 539.9588676784088, 'z_approx': -0.09137660035451177, 'p': 0.9271933541639341, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.33154871931409646}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': 0.03158367108005677, 'coef': 0.03158367108005677, '|coef|': 0.03158367108005677, 'se_metric': 1.1318986402129017, 'z_approx': 0.02790326797646485, 'p': 0.9777393019913578, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -5.433677521298333, 'coef': -5.433677521298333, '|coef|': 5.433677521298333, 'se_metric': 54.82868288432594, 'z_approx': -0.09910282785311401, 'p': 0.9210566268412212, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': 0.010487882939695754, 'coef': 0.010487882939695754, '|coef|': 0.010487882939695754, 'se_metric': 3.6895795589709146, 'z_approx': 0.0028425685832401456, 'p': 0.9977319614687759, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.997731961468776}

### 2025-09-12 07:52:00 — models_mixed

Métodos utilizados:
- Mixed-effects models: DV ~ KEC + length + position + frequency + surprisal?; random intercepts for subject; item variance component when possible.
- Controls included: length (token length), optional position and frequency (auto-detected or fallback local frequency), plus surprisal (surprisal_trf if available else surprisal).
- Benjamini-Hochberg FDR applied per dataset/file and per (file, DV).

Artefatos gerados:
- reports/v4.4/models_mixed_summary_v4.4.csv

Snapshot de resultados (top 10):
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': 2.0427669740387286, 'coef': 2.0427669740387286, '|coef|': 2.0427669740387286, 'se_metric': 20.447589604596043, 'z_approx': 0.09990258086848398, 'p': 0.9204216673674048, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.33154871931409646}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -1691.9240061847902, 'coef': -1691.9240061847902, '|coef|': 1691.9240061847902, 'se_metric': 1060.1844138684487, 'z_approx': -1.5958770795462098, 'p': 0.11051623977136549, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.33154871931409646}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'trt_ms', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': -49.33960565972466, 'coef': -49.33960565972466, '|coef|': 49.33960565972466, 'se_metric': 539.9588676784088, 'z_approx': -0.09137660035451177, 'p': 0.9271933541639341, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.33154871931409646}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'entropy', 'term': 'entropy', 'n': 415, 'coef_metric': 0.03158367108005677, 'coef': 0.03158367108005677, '|coef|': 0.03158367108005677, 'se_metric': 1.1318986402129017, 'z_approx': 0.02790326797646485, 'p': 0.9777393019913578, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'curvature', 'term': 'curvature', 'n': 415, 'coef_metric': -5.433677521298333, 'coef': -5.433677521298333, '|coef|': 5.433677521298333, 'se_metric': 54.82868288432594, 'z_approx': -0.09910282785311401, 'p': 0.9210566268412212, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 1.0}
- {'file': 'zuco_kec_rt.parquet', 'dataset': 'zuco', 'dv': 'nfix', 'metric': 'coherence', 'term': 'coherence', 'n': 509, 'coef_metric': 0.010487882939695754, 'coef': 0.010487882939695754, '|coef|': 0.010487882939695754, 'se_metric': 3.6895795589709146, 'z_approx': 0.0028425685832401456, 'p': 0.9977319614687759, 'converged': True, 'controls': 'length,surprisal,position,freq_local', 'random_effects': 'subject + item(vc)', 'method': 'mixedlm', 'q_fdr': 0.6630974386281929, 'q_fdr_by_dv': 0.997731961468776}

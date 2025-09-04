# Data Dictionary — L1 and L2

This document enumerates expected tables and columns for L1 (tidy) and L2 (derived) layers.

## L1 — swow_en_v1_tidy (CSV)
- cue: string
- response: string
- strength: float in [0,1]

Primary key: (cue, response)

## L1 — zuco_v2_tidy (CSV)
- subject: string
- sentence_id: int
- token_id: int
- gaze_duration_ms: float >= 0
- total_reading_time_ms: float >= 0

Primary key: (subject, sentence_id, token_id)

## L2 — ag5_kec_metrics (CSV)
- concept_id: string
- kec_score: float [0,1]
- coverage: float [0,1]
- density: float [0,1]

Primary key: (concept_id)


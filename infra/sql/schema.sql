-- BigQuery schema example for Darwin RAG++ documents table (v5.0)
-- Adjust dataset/table names externally.

CREATE TABLE IF NOT EXISTS `project.dataset.documents` (
  doc_id STRING NOT NULL,
  title STRING,
  content STRING,
  modality STRING, -- text|eeg|et
  lang STRING,
  embedding ARRAY<FLOAT64>,
  entropy FLOAT64,
  novelty_score FLOAT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS `project.dataset.citations` (
  citation_id STRING NOT NULL,
  doc_id STRING NOT NULL,
  query STRING,
  rank INT64,
  score FLOAT64,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Optional index-like helper using clustering (BigQuery):
-- CLUSTER BY lang, modality on documents table can accelerate filtered scans.

-- Example upsert pattern (pseudo):
-- MERGE `project.dataset.documents` T USING source S ON T.doc_id = S.doc_id
-- WHEN MATCHED THEN UPDATE SET content = S.content, embedding = S.embedding, entropy = S.entropy
-- WHEN NOT MATCHED THEN INSERT (doc_id, title, content, modality, lang, embedding, entropy, novelty_score) VALUES (...);

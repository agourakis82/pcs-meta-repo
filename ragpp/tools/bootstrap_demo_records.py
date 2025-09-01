import json
import os

base = "ragpp/data/processed/2025_sweep"
os.makedirs(base, exist_ok=True)

# 1) Chunks (Abstract como chunk)
chunk = {
    "chunk_id": "demo::abstract",
    "record_id": "doi:10.1234/demo.2025.0001",
    "section": "StructuredAbstract",
    "text": (
        "Background: Demo paper. Methods: small RCT. "
        "Results: signal present. Limitations: sample size."
    ),
}
with open(os.path.join(base, "YEAR-2025_chunks.jsonl"), "w", encoding="utf-8") as f:
    f.write(json.dumps(chunk) + "\n")

# 2) Notas RAG (structured abstract, QA e edges)
note = {
    "record_id": "doi:10.1234/demo.2025.0001",
    "structured_abstract": (
        "Objective: demo. PICO: P patients; I treatment; C placebo; "
        "O outcome. (DOI:10.1234/demo.2025.0001)"
    ),
    "qa_tsv": (
        "What design?\tSmall randomized trial\n"
        "What outcome?\tPrimary clinical outcome"
    ),
    "concept_edges": [
        {
            "source_entity": "TreatmentX",
            "relation": "improves",
            "target_entity": "OutcomeY",
            "evidence_span_ref": "Abstract",
        }
    ],
}
with open(
    os.path.join(base, "YEAR-2025_active_reading_notes.jsonl"), "w", encoding="utf-8"
) as f:
    f.write(json.dumps(note) + "\n")
print("Demo JSONL ok.")

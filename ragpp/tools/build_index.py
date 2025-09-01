import json, argparse
import logging
# Hard-disable Posthog telemetry used by Chroma (shim to avoid signature mismatch)
try:
    import posthog  # type: ignore

    def _posthog_capture_shim(*args, **kwargs):
        # Do nothing to suppress telemetry
        return None

    posthog.capture = _posthog_capture_shim  # type: ignore[attr-defined]
    posthog.disabled = True  # type: ignore[attr-defined]
except Exception:
    pass
import chromadb
from chromadb.config import Settings

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def main(db_path, chunks_path, notes_path):
    # Disable telemetry to avoid noisy warnings from ChromaDB in some environments
    # Silence Posthog telemetry logger used by Chroma before client creation
    logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )
    col = client.get_or_create_collection("lit2025")

    # 1) Chunks (Abstract por enquanto; depois OA full-text)
    docs, metas, ids = [], [], []
    for i, rec in enumerate(load_jsonl(chunks_path), start=1):
        txt = rec.get("text") or ""
        if not txt.strip(): continue
        rid = rec.get("record_id") or rec.get("id") or f"rec{i}"
        ids.append(f"chunk::{rid}::{i}")
        docs.append(txt)
        metas.append({
            "source":"chunk",
            "record_id": rid,
            "section": rec.get("section","Abstract")
        })
    if ids: col.add(ids=ids, documents=docs, metadatas=metas)

    # 2) Notas RAG (structured abstract, QA, concept edges em 1 blob por artigo)
    notes = load_jsonl(notes_path)
    docs, metas, ids = [], [], []
    for j, rec in enumerate(notes, start=1):
        rid = rec.get("record_id") or f"r{j}"
        blob = []
        if rec.get("structured_abstract"):
            blob.append("StructuredAbstract: " + rec["structured_abstract"])
        if rec.get("qa_tsv"):
            blob.append("QAs:\n" + rec["qa_tsv"])
        if rec.get("concept_edges"):
            edges = rec["concept_edges"]
            blob.append("ConceptEdges: " + "; ".join([f"{e['source_entity']}|{e['relation']}|{e['target_entity']}" for e in edges]))
        if not blob: continue
        ids.append(f"note::{rid}")
        docs.append("\n".join(blob))
        metas.append({"source":"notes","record_id":rid})
    if ids: col.add(ids=ids, documents=docs, metadatas=metas)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="ragpp/index/lit2025")
    p.add_argument("--chunks", default="ragpp/data/processed/2025_sweep/YEAR-2025_chunks.jsonl")
    p.add_argument("--notes",  default="ragpp/data/processed/2025_sweep/YEAR-2025_active_reading_notes.jsonl")
    a = p.parse_args()
    main(a.db, a.chunks, a.notes)

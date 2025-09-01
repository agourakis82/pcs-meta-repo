import chromadb
from chromadb.config import Settings
import logging

# Silence telemetry
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True

client = chromadb.PersistentClient(path="ragpp/index/lit2025", settings=Settings(allow_reset=False, anonymized_telemetry=False))
col = client.get_collection("lit2025")

print(f"Index inspection for collection 'lit2025':")
print(f"- Total records: {col.count()}")

if col.count() > 0:
    peek = col.peek(limit=3)
    print(f"- Sample IDs: {peek['ids']}")
    print(f"- Sample metadatas: {peek['metadatas']}")
    if peek['documents']:
        print(f"- Sample documents (first 200 chars): {[doc[:200] + '...' for doc in peek['documents']]}")

    # Sample query
    q = "demo paper"
    try:
        res = col.query(query_texts=[q], n_results=2)
        print(f"\nSample query: '{q}'")
        if res.get('documents') and res['documents'] and len(res['documents']) > 0 and res['documents'][0]:  # type: ignore
            for i, (doc, meta, _id) in enumerate(zip(res['documents'][0], res['metadatas'][0], res['ids'][0]), start=1):  # type: ignore
                print(f"[{i}] ID={_id} | {meta} | {doc[:300]}...")
        else:
            print("- No query results.")
    except Exception as e:
        print(f"- Query failed: {e}")
else:
    print("- No records found. Run bootstrap_demo_records.py and build_index.py first.")

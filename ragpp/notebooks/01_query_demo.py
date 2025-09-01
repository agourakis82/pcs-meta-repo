import chromadb
from chromadb.config import Settings
from ragpp.tools.router import pick_index

client = chromadb.PersistentClient(path="ragpp/index/lit2025", settings=Settings(allow_reset=False))
col   = client.get_collection("lit2025")

q = "Quais evidências 2025 ligam leitura natural (ZuCo) a métricas de EEG por banda?"
k = 5
res = col.query(query_texts=[q], n_results=k)
for i,(doc,meta,_id) in enumerate(zip(res['documents'][0],res['metadatas'][0],res['ids'][0]), start=1):
    print(f"\n[{i}] ID={_id} SECTION={meta.get('section')} SOURCE={meta.get('source')} | record_id={meta.get('record_id')}\n{doc[:600]}...")

# RAG++ Track — Project PCS (Symbolic First)

Goal: Consolidate repo + ChatGPT logs into a searchable, cited knowledge base for drafting/manuscripts.

## Indexing plan
- Sources: /docs, /reports, /manuscripts, selected /notebooks exports, and this digest.
- Chunking: 800–1200 tokens, overlap ~200; metadata: {path, version, date, QGate tags}.
- Embeddings: local or API; vector store (FAISS). 
- Citations: store source path/anchors; render repo-relative links.

## Pipelines
- index_build.py: crawl, chunk, embed, persist index.
- query_cli.py: query with metadata filters (e.g., SymbolicOnly=true).
- cite_resolve.py: map chunks back to canonical sources for Vancouver refs.

## Governance
- Public-only content; zero PII; license compliance.

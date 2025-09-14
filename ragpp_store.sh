#!/bin/bash
# Script para armazenar descobertas no RAG++

if [ $# -eq 0 ]; then
    echo "Uso: ./ragpp_store.sh 'sua descoberta aqui' [categoria] [tags...]"
    echo "Exemplo: ./ragpp_store.sh 'Nova descoberta sobre entropia' research_findings entropy semantic"
    exit 1
fi

CONTENT="$1"
CATEGORY="${2:-research_findings}"
shift 2
TAGS="$@"

echo "💾 Armazenando descoberta..."
echo "Categoria: $CATEGORY"
echo "Tags: $TAGS"
echo "=================================="

python ragpp/tools/mcp_rag_integration.py store --content "$CONTENT" --category "$CATEGORY" --tags $TAGS

#!/bin/bash
# Script de busca rápida RAG++

if [ $# -eq 0 ]; then
    echo "Uso: ./ragpp_search.sh 'sua pergunta aqui'"
    echo "Exemplo: ./ragpp_search.sh 'What is semantic entropy?'"
    exit 1
fi

QUERY="$1"
echo "🔍 Buscando: $QUERY"
echo "=================================="

python ragpp/tools/mcp_rag_integration.py qa --query "$QUERY"

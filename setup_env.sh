#!/bin/bash
# PCS Environment Setup
echo "🔧 Configurando ambiente PCS..."

# Google Cloud
export PROJECT_ID="pcs-helio"
export LOCATION="us-central1"

# Darwin Platform Local
export CONTEXT_CACHE_ENABLED="true"
export RAG_ENGINE_ENABLED="false"
export VECTOR_SEARCH_ENABLED="false"
export DEBUG="true"
export ENVIRONMENT="local"

# Add to current session
echo "✅ Variáveis de ambiente configuradas"
echo "📋 Para tornar permanente, adicione ao ~/.bashrc:"
echo "source $(pwd)/setup_env.sh"

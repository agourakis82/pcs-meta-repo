#!/bin/bash
# Script para garantir que gemini_direct_api.py está no deploy

# Verifica se o arquivo existe no diretório raiz
if [ ! -f "gemini_direct_api.py" ]; then
  echo "❌ O arquivo gemini_direct_api.py não foi encontrado no diretório raiz."
  exit 1
fi

# Verifica se a referência já existe no Dockerfile
if grep -q "COPY gemini_direct_api.py" Dockerfile; then
  echo "✅ Dockerfile já inclui gemini_direct_api.py"
else
  # Adiciona o comando COPY após a linha que copia o main.py
  echo "🔄 Adicionando gemini_direct_api.py ao Dockerfile..."
  sed -i '/COPY main.py/a COPY gemini_direct_api.py .' Dockerfile
  echo "✅ Dockerfile atualizado"
fi

echo "✅ Preparação concluída - gemini_direct_api.py será incluído no build"

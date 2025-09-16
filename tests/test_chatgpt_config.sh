#!/bin/bash

echo "🧪 Teste de Configuração ChatGPT - PCS Meta-Repo"
echo "============================================="
echo

# Configurações
BASE_URL="http://mcp.agourakis.med.br"  # Usando HTTP por enquanto
TOKEN="wlaKVi5Qf4RooUprwQqtWrAS_Laecy98-oUzs7AAn7Qo"

echo "📋 Informações de Configuração:"
echo "• URL Base: $BASE_URL"
echo "• Token: ${TOKEN:0:20}..." 
echo

echo "1️⃣ Testando Health Check..."
HEALTH=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/health")
if [ $? -eq 0 ] && echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ Health Check: OK"
    echo "   Status: $(echo "$HEALTH" | jq -r '.status // "N/A"')"
    echo "   Artigos: $(echo "$HEALTH" | jq -r '.indexed_articles // "N/A"')"
    echo "   Capacidades: $(echo "$HEALTH" | jq -r '.capabilities[]?' | tr '\n' ', ' | sed 's/,$//')"
else
    echo "❌ Health Check: FALHOU"
    echo "   Resposta: $HEALTH"
fi
echo

echo "2️⃣ Testando Busca..."
SEARCH_RESULT=$(curl -s -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query": "depression treatment", "max_results": 3}' \
    "$BASE_URL/search")

if [ $? -eq 0 ] && echo "$SEARCH_RESULT" | grep -q "results"; then
    echo "✅ Busca: OK"
    TOTAL=$(echo "$SEARCH_RESULT" | jq -r '.total_found // 0')
    TIME=$(echo "$SEARCH_RESULT" | jq -r '.query_time // 0')
    echo "   Resultados encontrados: $TOTAL"
    echo "   Tempo de busca: ${TIME}s"
    
    # Mostrar primeiro resultado
    FIRST_TITLE=$(echo "$SEARCH_RESULT" | jq -r '.results[0].title // "N/A"')
    echo "   Primeiro resultado: $FIRST_TITLE"
else
    echo "❌ Busca: FALHOU"
    echo "   Resposta: $SEARCH_RESULT"
fi
echo

echo "3️⃣ Configuração para ChatGPT:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "🔗 URL para Actions: $BASE_URL"
echo "🔑 Token: $TOKEN"
echo
echo "📋 Schema OpenAPI: Disponível em chatgpt_action_config.json"
echo "📖 Guia Completo: CHATGPT_CLOUDFLARE_SETUP.md"
echo

echo "4️⃣ Comandos de Teste no ChatGPT:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo '• "Verificar status do servidor de pesquisa"'
echo '• "Buscar artigos sobre machine learning em psiquiatria"'
echo '• "Encontrar pesquisas sobre neuroplasticity"'
echo '• "Pesquisar evidências sobre terapia cognitivo-comportamental"'
echo

if echo "$HEALTH" | grep -q "healthy" && echo "$SEARCH_RESULT" | grep -q "results"; then
    echo "🎉 CONFIGURAÇÃO PRONTA!"
    echo "   Todos os testes passaram. ChatGPT pode ser configurado agora."
else
    echo "⚠️  VERIFICAR PROBLEMAS"
    echo "   Alguns testes falharam. Verifique os logs acima."
fi

echo
echo "📞 Suporte: Verificar logs em /var/log/nginx/ se houver problemas"
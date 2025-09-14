#!/bin/bash
# -*- coding: utf-8 -*-
"""
Script para executar testes do sistema F1 - Testing and Validation
"""

echo "🧪 Executando Sistema F1 - Testes e Validação"
echo "============================================="

# Função para executar comando e verificar resultado
run_test() {
    local test_name="$1"
    local command="$2"
    
    echo "📋 Executando: $test_name"
    echo "   Comando: $command"
    
    if eval "$command"; then
        echo "✅ $test_name - PASSOU"
        return 0
    else
        echo "❌ $test_name - FALHOU"
        return 1
    fi
}

# Contadores
total_tests=0
passed_tests=0

echo
echo "1️⃣ Testes de Configuração"
echo "-------------------------"
((total_tests++))
if run_test "Importação de módulos" "python -c 'from api.config import Settings; from api.auth import extract_api_key; from api.cache import CacheManager; print(\"✅ Importações OK\")'"; then
    ((passed_tests++))
fi

echo
echo "2️⃣ Testes de Sintaxe"
echo "--------------------"
((total_tests++))
if run_test "Sintaxe dos testes" "python -m py_compile tests/conftest.py tests/unit/test_config.py tests/unit/test_auth.py tests/unit/test_cache.py tests/integration/test_api_endpoints.py"; then
    ((passed_tests++))
fi

echo
echo "3️⃣ Testes Básicos de API"
echo "------------------------"
((total_tests++))
if run_test "Health Check" "python -c 'from fastapi.testclient import TestClient; from api.main import app; client = TestClient(app); r = client.get(\"/\"); assert r.status_code == 200; print(\"✅ Health check OK\")'"; then
    ((passed_tests++))
fi

echo
echo "4️⃣ Validação de Estrutura"
echo "-------------------------"
((total_tests++))
if run_test "Estrutura de diretórios" "test -d tests/unit && test -d tests/integration && test -f tests/__init__.py && test -f tests/conftest.py && echo '✅ Estrutura OK'"; then
    ((passed_tests++))
fi

echo
echo "5️⃣ Testes de Configuração"
echo "-------------------------"
((total_tests++))
if run_test "Configurações padrão" "python -c 'from api.config import Settings; s = Settings(); assert s.API_NAME == \"PCS‑HELIO MCP API\"; assert s.ENV == \"development\"; print(\"✅ Configurações OK\")'"; then
    ((passed_tests++))
fi

echo
echo "6️⃣ Validação de Cache"
echo "---------------------"
((total_tests++))
if run_test "Cache Memory" "python -c 'from api.cache import MemoryCache; c = MemoryCache(); print(\"✅ MemoryCache OK\")'"; then
    ((passed_tests++))
fi

echo
echo "7️⃣ Validação de Auth"
echo "--------------------"
((total_tests++))
if run_test "Sistema Auth" "python -c 'from api.auth import extract_api_key; from fastapi import Request; from unittest.mock import MagicMock; r = MagicMock(); r.headers = {}; r.query_params = {}; assert extract_api_key(r) is None; print(\"✅ Auth OK\")'"; then
    ((passed_tests++))
fi

echo
echo "8️⃣ Validação Final"
echo "------------------"
((total_tests++))
if run_test "Sistema Completo" "python -c 'from api.main import app; from fastapi.testclient import TestClient; c = TestClient(app); assert c.get(\"/\").status_code == 200; print(\"✅ Sistema Completo OK\")'"; then
    ((passed_tests++))
fi

# Resultado final
echo
echo "📊 RESULTADO DOS TESTES F1"
echo "=========================="
echo "Total de testes: $total_tests"
echo "Testes aprovados: $passed_tests"
echo "Testes falharam: $((total_tests - passed_tests))"

if [ $passed_tests -eq $total_tests ]; then
    echo "🎉 TODOS OS TESTES PASSARAM!"
    echo "✅ Sistema F1 - Testes e Validação COMPLETO"
    exit 0
else
    echo "⚠️  Alguns testes falharam"
    echo "Taxa de sucesso: $(( passed_tests * 100 / total_tests ))%"
    exit 1
fi
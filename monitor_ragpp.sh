#!/bin/bash
# RAG++ Production Monitor
# Monitora a saúde e performance do servidor RAG++

set -e

# Configurações
SERVICE_NAME="ragpp"
BASE_URL="http://localhost:8000"
LOG_FILE="/var/log/ragpp_monitor.log"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função de log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar status do serviço
check_service() {
    log "Verificando status do serviço..."
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        success "Serviço $SERVICE_NAME está ativo"
        return 0
    else
        error "Serviço $SERVICE_NAME está inativo"
        return 1
    fi
}

# Verificar conectividade HTTP
check_http() {
    log "Verificando conectividade HTTP..."
    if curl -s --max-time 5 "$BASE_URL/health" > /dev/null; then
        success "HTTP endpoint acessível"
        return 0
    else
        error "HTTP endpoint não acessível"
        return 1
    fi
}

# Verificar saúde da API
check_health() {
    log "Verificando saúde da API..."
    response=$(curl -s --max-time 10 "$BASE_URL/health")
    if [ $? -eq 0 ] && echo "$response" | grep -q "healthy"; then
        success "API saudável"
        return 0
    else
        error "API não saudável"
        return 1
    fi
}

# Verificar estatísticas do cache
check_cache() {
    log "Verificando cache..."
    response=$(curl -s --max-time 10 "$BASE_URL/cache/stats")
    if [ $? -eq 0 ]; then
        cache_size=$(echo "$response" | grep -o '"size":[0-9]*' | cut -d':' -f2)
        hit_rate=$(echo "$response" | grep -o '"hit_rate":[0-9.]*' | cut -d':' -f2)

        if [ "$cache_size" != "" ]; then
            success "Cache ativo - Tamanho: $cache_size, Hit Rate: ${hit_rate}%"
            return 0
        fi
    fi

    warning "Cache não disponível ou inativo"
    return 1
}

# Verificar uso de recursos
check_resources() {
    log "Verificando uso de recursos..."

    # CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    cpu_int=${cpu_usage%.*}

    # Memória
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')

    # Disco
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

    echo "📊 Recursos - CPU: ${cpu_int}%, RAM: ${mem_usage}%, Disco: ${disk_usage}%"

    # Alertas
    if [ "$cpu_int" -gt 90 ]; then
        warning "CPU muito alta: ${cpu_int}%"
    fi

    if [ "$mem_usage" -gt 90 ]; then
        warning "Memória muito alta: ${mem_usage}%"
    fi

    if [ "$disk_usage" -gt 90 ]; then
        warning "Disco muito cheio: ${disk_usage}%"
    fi
}

# Verificar logs por erros
check_logs() {
    log "Verificando logs por erros..."
    errors=$(journalctl -u "$SERVICE_NAME" --since "1 hour ago" -q | grep -i error | wc -l)

    if [ "$errors" -gt 0 ]; then
        warning "Encontrados $errors erros nos logs da última hora"
        # Mostrar últimas 5 linhas de erro
        journalctl -u "$SERVICE_NAME" --since "1 hour ago" -q | grep -i error | tail -5
    else
        success "Nenhum erro encontrado nos logs"
    fi
}

# Teste de performance básico
performance_test() {
    log "Executando teste de performance..."

    # Tempo de resposta health
    start=$(date +%s.%3N)
    curl -s "$BASE_URL/health" > /dev/null
    end=$(date +%s.%3N)
    health_time=$(echo "$end - $start" | bc)

    # Tempo de resposta cache stats
    start=$(date +%s.%3N)
    curl -s "$BASE_URL/cache/stats" > /dev/null
    end=$(date +%s.%3N)
    cache_time=$(echo "$end - $start" | bc)

    echo "⏱️ Performance - Health: ${health_time}s, Cache: ${cache_time}s"

    # Alertas de performance
    if (( $(echo "$health_time > 1.0" | bc -l) )); then
        warning "Health endpoint lento: ${health_time}s"
    fi
}

# Função principal
main() {
    echo "🔍 RAG++ Production Monitor"
    echo "============================"

    local failed_checks=0

    # Executar verificações
    check_service || ((failed_checks++))
    check_http || ((failed_checks++))
    check_health || ((failed_checks++))
    check_cache || ((failed_checks++))
    check_resources
    check_logs
    performance_test

    echo ""
    if [ $failed_checks -eq 0 ]; then
        success "🎉 Todas as verificações passaram!"
        exit 0
    else
        error "❌ $failed_checks verificações falharam"
        exit 1
    fi
}

# Executar apenas se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
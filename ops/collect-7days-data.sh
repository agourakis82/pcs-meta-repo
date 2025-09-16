#!/bin/bash
# Sistema de Coleta de Dados dos Últimos 7 Dias
# Coleta mudanças, cálculos, progressos e erros do sistema PCS Meta Repo
# Usage: ./collect-7days-data.sh [--output-format json|markdown|csv]

set -euo pipefail

# === CONFIGURAÇÃO ===
DAYS_BACK=7
OUTPUT_DIR="/tmp/pcs-7days-analysis"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_FORMAT="${1:-json}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Criar diretório de saída
mkdir -p "$OUTPUT_DIR"

log "=== INICIANDO COLETA DE DADOS DOS ÚLTIMOS $DAYS_BACK DIAS ==="

# 1. COLETA DE MUDANÇAS GIT
collect_git_changes() {
    log "Coletando mudanças Git dos últimos $DAYS_BACK dias..."
    
    local git_data_file="$OUTPUT_DIR/git_changes_${TIMESTAMP}.json"
    local since_date=$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')
    
    {
        echo "{"
        echo "  \"collection_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"period\": \"$DAYS_BACK days\","
        echo "  \"since_date\": \"$since_date\","
        echo "  \"repository\": \"$(pwd)\","
        echo "  \"commits\": ["
        
        local first_commit=true
        git log --since="$since_date" --pretty=format:'%H|%an|%ae|%ad|%s' --date=iso | while IFS='|' read -r hash author email date message; do
            if [[ "$first_commit" == "true" ]]; then
                first_commit=false
            else
                echo ","
            fi
            
            echo "    {"
            echo "      \"hash\": \"$hash\","
            echo "      \"author\": \"$author\","
            echo "      \"email\": \"$email\","
            echo "      \"date\": \"$date\","
            echo "      \"message\": \"$(echo "$message" | sed 's/"/\\"/g')\","
            echo "      \"files_changed\": ["
            
            local first_file=true
            git show --name-only --pretty=format: "$hash" | grep -v '^$' | while read -r file; do
                if [[ "$first_file" == "true" ]]; then
                    first_file=false
                else
                    echo ","
                fi
                echo "        \"$file\""
            done
            
            echo "      ],"
            echo "      \"stats\": {"
            local stats=$(git show --stat "$hash" | tail -1)
            echo "        \"summary\": \"$stats\""
            echo "      }"
            echo -n "    }"
        done
        
        echo ""
        echo "  ],"
        
        # Estatísticas gerais
        local total_commits=$(git rev-list --count --since="$since_date" HEAD)
        local total_authors=$(git log --since="$since_date" --pretty=format:'%an' | sort -u | wc -l)
        local files_changed=$(git log --since="$since_date" --name-only --pretty=format: | grep -v '^$' | sort -u | wc -l)
        
        echo "  \"statistics\": {"
        echo "    \"total_commits\": $total_commits,"
        echo "    \"total_authors\": $total_authors,"
        echo "    \"files_changed\": $files_changed,"
        echo "    \"lines_added\": $(git log --since="$since_date" --numstat --pretty=format: | awk '{added+=$1} END {print added+0}'),"
        echo "    \"lines_deleted\": $(git log --since="$since_date" --numstat --pretty=format: | awk '{deleted+=$2} END {print deleted+0}')"
        echo "  }"
        echo "}"
    } > "$git_data_file"
    
    success "Dados Git salvos em: $git_data_file"
}

# 2. COLETA DE LOGS DO SISTEMA
collect_system_logs() {
    log "Coletando logs do sistema dos últimos $DAYS_BACK dias..."
    
    local logs_file="$OUTPUT_DIR/system_logs_${TIMESTAMP}.json"
    local since_date=$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')
    
    {
        echo "{"
        echo "  \"collection_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"period\": \"$DAYS_BACK days\","
        echo "  \"logs\": {"
        
        # Logs do nginx
        echo "    \"nginx\": {"
        if [[ -f /var/log/nginx/access.log ]]; then
            echo "      \"access_log_entries\": $(grep "$(date -d "$DAYS_BACK days ago" '+%d/%b/%Y')" /var/log/nginx/access.log 2>/dev/null | wc -l),"
            echo "      \"error_log_entries\": $(grep "$(date -d "$DAYS_BACK days ago" '+%Y/%m/%d')" /var/log/nginx/error.log 2>/dev/null | wc -l),"
            echo "      \"status_codes\": {"
            awk -v since="$since_date" '$4 >= "["since {print $9}' /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | awk '
                BEGIN{first=1}
                {
                    if(first) first=0; else printf(",");
                    printf("\n        \"%s\": %d", $2, $1)
                }
                END{if(!first) printf("\n      ")}
            '
            echo "      }"
        else
            echo "      \"status\": \"log_file_not_found\""
        fi
        echo "    },"
        
        # Logs do cloudflared
        echo "    \"cloudflared\": {"
        if [[ -f /var/log/cloudflared.log ]]; then
            echo "      \"total_entries\": $(grep "$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')" /var/log/cloudflared.log 2>/dev/null | wc -l),"
            echo "      \"error_entries\": $(grep -i error /var/log/cloudflared.log 2>/dev/null | grep "$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')" | wc -l)"
        else
            echo "      \"status\": \"log_file_not_found\""
        fi
        echo "    },"
        
        # Logs do systemd para ragpp-mcp-server
        echo "    \"ragpp_mcp_server\": {"
        local service_logs=$(journalctl -u ragpp-mcp-server --since="$since_date" --no-pager -o json 2>/dev/null | wc -l)
        echo "      \"total_entries\": $service_logs,"
        local error_logs=$(journalctl -u ragpp-mcp-server --since="$since_date" --no-pager -p err 2>/dev/null | wc -l)
        echo "      \"error_entries\": $error_logs"
        echo "    }"
        
        echo "  }"
        echo "}"
    } > "$logs_file"
    
    success "Logs do sistema salvos em: $logs_file"
}

# 3. COLETA DE MÉTRICAS DE PERFORMANCE
collect_performance_metrics() {
    log "Coletando métricas de performance..."
    
    local metrics_file="$OUTPUT_DIR/performance_metrics_${TIMESTAMP}.json"
    
    {
        echo "{"
        echo "  \"collection_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"system_metrics\": {"
        echo "    \"cpu_usage\": $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'),"
        echo "    \"memory_usage\": {"
        echo "      \"total_mb\": $(free -m | awk 'NR==2{printf "%.0f", $2}'),"
        echo "      \"used_mb\": $(free -m | awk 'NR==2{printf "%.0f", $3}'),"
        echo "      \"free_mb\": $(free -m | awk 'NR==2{printf "%.0f", $4}'),"
        echo "      \"usage_percent\": $(free | awk 'NR==2{printf "%.1f", $3*100/$2}')"
        echo "    },"
        echo "    \"disk_usage\": {"
        echo "      \"total_gb\": $(df -BG / | awk 'NR==2{print $2}' | sed 's/G//'),"
        echo "      \"used_gb\": $(df -BG / | awk 'NR==2{print $3}' | sed 's/G//'),"
        echo "      \"available_gb\": $(df -BG / | awk 'NR==2{print $4}' | sed 's/G//'),"
        echo "      \"usage_percent\": $(df / | awk 'NR==2{print $5}' | sed 's/%//')"
        echo "    },"
        echo "    \"load_average\": {"
        local load_avg=$(uptime | awk -F'load average:' '{print $2}')
        echo "      \"1min\": $(echo $load_avg | awk '{print $1}' | sed 's/,//'),"
        echo "      \"5min\": $(echo $load_avg | awk '{print $2}' | sed 's/,//'),"
        echo "      \"15min\": $(echo $load_avg | awk '{print $3}')"
        echo "    }"
        echo "  },"
        
        # Teste de endpoints
        echo "  \"endpoint_tests\": {"
        local start_time=$(date +%s.%N)
        local health_status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        
        echo "    \"backend_health\": {"
        echo "      \"status_code\": \"$health_status\","
        echo "      \"response_time_ms\": $(echo "$response_time * 1000" | bc -l | cut -d. -f1)"
        echo "    },"
        
        # Teste nginx interno
        start_time=$(date +%s.%N)
        local nginx_status=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/ 2>/dev/null || echo "000")
        end_time=$(date +%s.%N)
        response_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        
        echo "    \"nginx_internal\": {"
        echo "      \"status_code\": \"$nginx_status\","
        echo "      \"response_time_ms\": $(echo "$response_time * 1000" | bc -l | cut -d. -f1)"
        echo "    },"
        
        # Teste externo MCP
        start_time=$(date +%s.%N)
        local mcp_status=$(curl -s -o /dev/null -w "%{http_code}" https://mcp.agourakis.med.br/health 2>/dev/null || echo "000")
        end_time=$(date +%s.%N)
        response_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        
        echo "    \"mcp_external\": {"
        echo "      \"status_code\": \"$mcp_status\","
        echo "      \"response_time_ms\": $(echo "$response_time * 1000" | bc -l | cut -d. -f1)"
        echo "    }"
        echo "  }"
        echo "}"
    } > "$metrics_file"
    
    success "Métricas de performance salvos em: $metrics_file"
}

# 4. ANÁLISE DE ERROS E PROBLEMAS
collect_error_analysis() {
    log "Analisando erros e problemas dos últimos $DAYS_BACK dias..."
    
    local errors_file="$OUTPUT_DIR/error_analysis_${TIMESTAMP}.json"
    local since_date=$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')
    
    {
        echo "{"
        echo "  \"collection_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"error_analysis\": {"
        
        # Análise de logs de erro do nginx
        echo "    \"nginx_errors\": ["
        if [[ -f /var/log/nginx/error.log ]]; then
            local nginx_errors=""
            while IFS= read -r line; do
                if [[ -n "$line" ]]; then
                    nginx_errors="${nginx_errors}      \"$(echo "$line" | sed 's/"/\\"/g')\",\n"
                fi
            done < <(grep "$since_date" /var/log/nginx/error.log 2>/dev/null | head -20)
            
            if [[ -n "$nginx_errors" ]]; then
                echo -e "${nginx_errors%,\\n}"
            fi
        fi
        echo "    ],"
        
        # Análise de logs do systemd
        echo "    \"systemd_errors\": ["
        local systemd_errors=""
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                systemd_errors="${systemd_errors}      $line,\n"
            fi
        done < <(journalctl --since="$since_date" -p err --no-pager -o json 2>/dev/null | head -10)
        
        if [[ -n "$systemd_errors" ]]; then
            echo -e "${systemd_errors%,\\n}"
        fi
        echo "    ],"
        
        # Verificação de serviços críticos
        echo "    \"service_status\": {"
        echo "      \"nginx\": \"$(systemctl is-active nginx 2>/dev/null || echo 'unknown')\","
        echo "      \"cloudflared\": \"$(systemctl is-active cloudflared 2>/dev/null || echo 'unknown')\","
        echo "      \"ragpp-mcp-server\": \"$(systemctl is-active ragpp-mcp-server 2>/dev/null || echo 'unknown')\""
        echo "    },"
        
        # Análise de conectividade
        echo "    \"connectivity_tests\": {"
        echo "      \"dns_resolution\": {"
        echo "        \"www_agourakis_med_br\": \"$(dig +short www.agourakis.med.br 2>/dev/null | wc -l)\","
        echo "        \"mcp_agourakis_med_br\": \"$(dig +short mcp.agourakis.med.br 2>/dev/null | wc -l)\""
        echo "      },"
        echo "      \"port_tests\": {"
        echo "        \"port_8000_backend\": \"$(nc -z 127.0.0.1 8000 2>/dev/null && echo 'open' || echo 'closed')\","
        echo "        \"port_8080_nginx\": \"$(nc -z 127.0.0.1 8080 2>/dev/null && echo 'open' || echo 'closed')\""
        echo "      }"
        echo "    }"
        
        echo "  }"
        echo "}"
    } > "$errors_file"
    
    success "Análise de erros salva em: $errors_file"
}

# 5. COLETA DE MUDANÇAS DE CONFIGURAÇÃO
collect_config_changes() {
    log "Analisando mudanças de configuração..."
    
    local config_file="$OUTPUT_DIR/config_changes_${TIMESTAMP}.json"
    local since_date=$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')
    
    {
        echo "{"
        echo "  \"collection_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"configuration_files\": {"
        
        # Nginx configs
        echo "    \"nginx\": {"
        if [[ -f /etc/nginx/nginx.conf ]]; then
            echo "      \"main_config_modified\": \"$(stat -c %y /etc/nginx/nginx.conf)\","
            echo "      \"sites_enabled\": ["
            find /etc/nginx/sites-enabled/ -type f -name "*.conf" 2>/dev/null | while read -r file; do
                echo "        {"
                echo "          \"file\": \"$file\","
                echo "          \"modified\": \"$(stat -c %y "$file")\""
                echo "        },"
            done | sed '$ s/,$//'
            echo "      ]"
        else
            echo "      \"status\": \"not_found\""
        fi
        echo "    },"
        
        # Cloudflared config
        echo "    \"cloudflared\": {"
        if [[ -f /etc/cloudflared/config.yml ]]; then
            echo "      \"config_modified\": \"$(stat -c %y /etc/cloudflared/config.yml)\","
            echo "      \"config_size_bytes\": $(stat -c %s /etc/cloudflared/config.yml)"
        else
            echo "      \"status\": \"not_found\""
        fi
        echo "    },"
        
        # Systemd services
        echo "    \"systemd_services\": {"
        if [[ -f /etc/systemd/system/ragpp-mcp-server.service ]]; then
            echo "      \"ragpp_service_modified\": \"$(stat -c %y /etc/systemd/system/ragpp-mcp-server.service)\""
        else
            echo "      \"ragpp_service\": \"not_found\""
        fi
        echo "    }"
        
        echo "  }"
        echo "}"
    } > "$config_file"
    
    success "Mudanças de configuração salvas em: $config_file"
}

# 6. GERAR RELATÓRIO CONSOLIDADO
generate_consolidated_report() {
    log "Gerando relatório consolidado..."
    
    local report_file="$OUTPUT_DIR/consolidated_report_${TIMESTAMP}.json"
    
    {
        echo "{"
        echo "  \"report_metadata\": {"
        echo "    \"generated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "    \"period_days\": $DAYS_BACK,"
        echo "    \"hostname\": \"$(hostname)\","
        echo "    \"system_info\": {"
        echo "      \"os\": \"$(lsb_release -d 2>/dev/null | cut -f2 || uname -o)\","
        echo "      \"kernel\": \"$(uname -r)\","
        echo "      \"uptime\": \"$(uptime -p)\""
        echo "    }"
        echo "  },"
        
        # Incluir dados de todos os arquivos gerados
        echo "  \"data_files\": ["
        find "$OUTPUT_DIR" -name "*_${TIMESTAMP}.json" | while read -r file; do
            echo "    \"$(basename "$file")\","
        done | sed '$ s/,$//'
        echo "  ],"
        
        # Resumo executivo
        echo "  \"executive_summary\": {"
        local total_commits=$(git rev-list --count --since="$(date -d "$DAYS_BACK days ago" '+%Y-%m-%d')" HEAD 2>/dev/null || echo 0)
        echo "    \"total_commits_period\": $total_commits,"
        
        local nginx_errors=$(grep "$(date -d "$DAYS_BACK days ago" '+%Y/%m/%d')" /var/log/nginx/error.log 2>/dev/null | wc -l)
        echo "    \"nginx_errors_period\": $nginx_errors,"
        
        echo "    \"services_status\": {"
        echo "      \"all_services_running\": $(systemctl is-active nginx cloudflared ragpp-mcp-server 2>/dev/null | grep -c active || echo 0),"
        echo "      \"total_critical_services\": 3"
        echo "    },"
        
        echo "    \"connectivity_health\": {"
        local external_health=$(curl -s -o /dev/null -w "%{http_code}" https://mcp.agourakis.med.br/health 2>/dev/null)
        echo "      \"external_api_accessible\": $([ "$external_health" = "200" ] && echo 'true' || echo 'false'),"
        local internal_health=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null)
        echo "      \"internal_api_accessible\": $([ "$internal_health" = "200" ] && echo 'true' || echo 'false')"
        echo "    }"
        echo "  }"
        echo "}"
    } > "$report_file"
    
    success "Relatório consolidado salvo em: $report_file"
}

# 7. ALIMENTAR SERVIDOR COM DADOS
feed_server_with_data() {
    log "Alimentando servidor com dados coletados..."
    
    local feed_endpoint="http://127.0.0.1:8000/admin/feed-analysis-data"
    local consolidated_report="$OUTPUT_DIR/consolidated_report_${TIMESTAMP}.json"
    
    if [[ -f "$consolidated_report" ]]; then
        # Tentar enviar dados para o servidor
        local response=$(curl -s -X POST "$feed_endpoint" \
            -H "Content-Type: application/json" \
            -d @"$consolidated_report" \
            -w "%{http_code}" 2>/dev/null || echo "000")
        
        if [[ "$response" == *"200"* ]] || [[ "$response" == *"201"* ]]; then
            success "Dados enviados com sucesso para o servidor"
        else
            warning "Falha ao enviar dados para o servidor (código: $response)"
            log "Dados salvos localmente em: $OUTPUT_DIR"
        fi
    else
        error "Relatório consolidado não encontrado"
    fi
}

# EXECUÇÃO PRINCIPAL
main() {
    echo "=============================================="
    echo "   COLETA DE DADOS DOS ÚLTIMOS $DAYS_BACK DIAS"
    echo "=============================================="
    echo ""
    
    # Executar todas as coletas
    collect_git_changes
    collect_system_logs
    collect_performance_metrics
    collect_error_analysis
    collect_config_changes
    generate_consolidated_report
    
    # Tentar alimentar o servidor
    feed_server_with_data
    
    echo ""
    success "Coleta de dados concluída!"
    echo ""
    echo "📁 Dados salvos em: $OUTPUT_DIR"
    echo "📊 Arquivos gerados:"
    ls -la "$OUTPUT_DIR"/*_${TIMESTAMP}.json | awk '{print "   " $9 " (" $5 " bytes)"}'
    echo ""
    echo "🔄 Para enviar dados manualmente ao servidor:"
    echo "   curl -X POST http://127.0.0.1:8000/admin/feed-analysis-data \\"
    echo "        -H 'Content-Type: application/json' \\"
    echo "        -d @$OUTPUT_DIR/consolidated_report_${TIMESTAMP}.json"
}

# Tratamento de erros
trap 'error "Script interrompido"; exit 1' INT TERM

# Executar
main "$@"
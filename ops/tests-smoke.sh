#!/bin/bash
# Smoke Tests for Production Infrastructure
# Tests website, API endpoints, and SSE functionality
# Usage: ./tests-smoke.sh [--verbose] [--endpoint-only] [--sse-test]

set -euo pipefail

# === CONFIGURATION VARIABLES ===
ORG_DOMAIN="agourakis.med.br"
WWW_HOST="www.agourakis.med.br"
MCP_HOST="mcp.agourakis.med.br"
INTERNAL_WWW_PORT=8440
INTERNAL_MCP_PORT=8480
BACKEND_PORT=8000

# Test configuration
TIMEOUT_SHORT=10
TIMEOUT_LONG=30
SSE_TEST_DURATION=15

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Test result tracking
test_start() {
    ((TOTAL_TESTS++))
    log "Test $TOTAL_TESTS: $1"
}

test_pass() {
    ((PASSED_TESTS++))
    success "✓ $1"
}

test_fail() {
    ((FAILED_TESTS++))
    error "✗ $1"
}

# DNS Resolution Tests
test_dns_resolution() {
    log "=== DNS RESOLUTION TESTS ==="
    
    local hosts=("$WWW_HOST" "$MCP_HOST" "$ORG_DOMAIN")
    
    for host in "${hosts[@]}"; do
        test_start "DNS resolution for $host"
        
        if dig +short "$host" | grep -q .; then
            local ips=$(dig +short "$host" | tr '\n' ' ' | xargs)
            test_pass "$host resolves to: $ips"
        else
            test_fail "$host does not resolve"
        fi
    done
}

# SSL/TLS Certificate Tests
test_ssl_certificates() {
    log "=== SSL/TLS CERTIFICATE TESTS ==="
    
    local hosts=("$WWW_HOST" "$MCP_HOST")
    
    for host in "${hosts[@]}"; do
        test_start "SSL certificate for $host"
        
        if timeout "$TIMEOUT_SHORT" openssl s_client -connect "$host:443" -servername "$host" </dev/null 2>/dev/null | openssl x509 -noout -subject >/dev/null 2>&1; then
            local cert_info=$(timeout "$TIMEOUT_SHORT" openssl s_client -connect "$host:443" -servername "$host" </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer 2>/dev/null || echo "Could not retrieve cert info")
            test_pass "$host has valid SSL certificate"
            info "Certificate info: $cert_info"
        else
            test_fail "$host SSL certificate test failed"
        fi
    done
}

# Internal Endpoint Tests
test_internal_endpoints() {
    log "=== INTERNAL ENDPOINT TESTS ==="
    
    # Test internal nginx ports
    local endpoints=(
        "127.0.0.1:$INTERNAL_WWW_PORT|WWW Internal"
        "127.0.0.1:$INTERNAL_MCP_PORT|MCP Internal"
        "127.0.0.1:$BACKEND_PORT|Backend FastAPI"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local addr=$(echo "$endpoint" | cut -d'|' -f1)
        local name=$(echo "$endpoint" | cut -d'|' -f2)
        
        test_start "$name endpoint connectivity"
        
        if timeout "$TIMEOUT_SHORT" curl -s -I "http://$addr/" >/dev/null 2>&1; then
            test_pass "$name is responding at $addr"
        else
            test_fail "$name is not responding at $addr"
        fi
    done
}

# External Website Tests  
test_external_website() {
    log "=== EXTERNAL WEBSITE TESTS ==="
    
    # Test main website
    test_start "WWW website accessibility"
    local www_response=$(timeout "$TIMEOUT_SHORT" curl -s -I "https://$WWW_HOST/" 2>/dev/null | head -1 || echo "Connection failed")
    if echo "$www_response" | grep -q "200\|301\|302"; then
        test_pass "WWW website is accessible: $www_response"
    else
        test_fail "WWW website is not accessible: $www_response"
    fi
    
    # Test apex redirect
    test_start "Apex domain redirect"
    local apex_response=$(timeout "$TIMEOUT_SHORT" curl -s -I "https://$ORG_DOMAIN/" 2>/dev/null | head -1 || echo "Connection failed")
    if echo "$apex_response" | grep -q "301\|302"; then
        test_pass "Apex domain redirects correctly: $apex_response"
    else
        test_fail "Apex domain redirect issue: $apex_response"
    fi
}

# API Health Tests
test_api_health() {
    log "=== API HEALTH TESTS ==="
    
    # Test health endpoint
    test_start "MCP API health endpoint"
    local health_response=$(timeout "$TIMEOUT_SHORT" curl -s "https://$MCP_HOST/health" 2>/dev/null || echo "Connection failed")
    if echo "$health_response" | grep -q "OK\|healthy\|running"; then
        test_pass "MCP API health endpoint is working"
    else
        test_fail "MCP API health endpoint failed: $health_response"
    fi
    
    # Test OpenAPI schema
    test_start "OpenAPI schema endpoint"
    if timeout "$TIMEOUT_SHORT" curl -s "https://$MCP_HOST/openapi.json" 2>/dev/null | jq . >/dev/null 2>&1; then
        test_pass "OpenAPI schema is valid JSON"
    else
        test_fail "OpenAPI schema is invalid or not accessible"
    fi
}

# ChatGPT Actions Schema Test
test_chatgpt_schema() {
    log "=== CHATGPT ACTIONS SCHEMA TESTS ==="
    
    test_start "ChatGPT Actions schema endpoint"
    local schema_response=$(timeout "$TIMEOUT_SHORT" curl -s "https://$MCP_HOST/actions/schema/noauth" 2>/dev/null || echo "Connection failed")
    
    if echo "$schema_response" | jq . >/dev/null 2>&1; then
        test_pass "ChatGPT Actions schema is valid JSON"
        
        # Check for required fields
        if echo "$schema_response" | jq -e '.openapi' >/dev/null 2>&1; then
            test_pass "Schema contains OpenAPI version"
        else
            test_fail "Schema missing OpenAPI version"
        fi
        
        if echo "$schema_response" | jq -e '.paths' >/dev/null 2>&1; then
            test_pass "Schema contains API paths"
        else
            test_fail "Schema missing API paths"
        fi
    else
        test_fail "ChatGPT Actions schema is invalid: $schema_response"
    fi
}

# API Functionality Tests
test_api_functionality() {
    log "=== API FUNCTIONALITY TESTS ==="
    
    # Test search endpoint with POST
    test_start "MCP search endpoint"
    local search_data='{"query": "test query", "max_results": 3}'
    local search_response=$(timeout "$TIMEOUT_LONG" curl -s -X POST "https://$MCP_HOST/search" \
        -H "Content-Type: application/json" \
        -d "$search_data" 2>/dev/null || echo "Connection failed")
    
    if echo "$search_response" | jq . >/dev/null 2>&1; then
        test_pass "MCP search endpoint returns valid JSON"
    else
        test_fail "MCP search endpoint failed: $search_response"
    fi
    
    # Test CORS headers
    test_start "CORS headers on MCP endpoints"
    local cors_headers=$(timeout "$TIMEOUT_SHORT" curl -s -I "https://$MCP_HOST/health" 2>/dev/null | grep -i "access-control" || echo "No CORS headers")
    if echo "$cors_headers" | grep -q "Access-Control-Allow-Origin"; then
        test_pass "CORS headers are present"
    else
        test_fail "CORS headers are missing: $cors_headers"
    fi
}

# SSE Endpoint Test
test_sse_endpoint() {
    log "=== SSE ENDPOINT TESTS ==="
    
    test_start "SSE endpoint connectivity"
    
    # Create temporary file for SSE output
    local sse_output=$(mktemp)
    local sse_pid=""
    
    # Start SSE connection in background
    timeout "$SSE_TEST_DURATION" curl -s "https://$MCP_HOST/sse/events" > "$sse_output" 2>/dev/null &
    sse_pid=$!
    
    # Wait a moment for connection to establish
    sleep 3
    
    # Check if process is still running (good sign for SSE)
    if kill -0 "$sse_pid" 2>/dev/null; then
        test_pass "SSE connection established and maintained"
        
        # Let it run for a bit more then clean up
        sleep 2
        kill "$sse_pid" 2>/dev/null || true
        wait "$sse_pid" 2>/dev/null || true
        
        # Check if we received any SSE data
        if [[ -s "$sse_output" ]]; then
            test_pass "SSE endpoint returned data"
            info "SSE data sample: $(head -1 "$sse_output" | cut -c1-50)..."
        else
            warning "SSE endpoint connected but no data received (may be expected)"
        fi
    else
        test_fail "SSE connection failed immediately"
    fi
    
    # Cleanup
    rm -f "$sse_output"
}

# Performance Tests
test_response_times() {
    log "=== RESPONSE TIME TESTS ==="
    
    local endpoints=(
        "https://$WWW_HOST/|WWW Homepage"
        "https://$MCP_HOST/health|MCP Health"
        "https://$MCP_HOST/openapi.json|OpenAPI Schema"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url=$(echo "$endpoint" | cut -d'|' -f1)
        local name=$(echo "$endpoint" | cut -d'|' -f2)
        
        test_start "$name response time"
        
        local response_time=$(timeout "$TIMEOUT_SHORT" curl -s -w "%{time_total}" -o /dev/null "$url" 2>/dev/null || echo "failed")
        
        if [[ "$response_time" != "failed" ]]; then
            # Convert to milliseconds for easier reading
            local ms_time=$(echo "$response_time * 1000" | bc -l 2>/dev/null | cut -d. -f1 2>/dev/null || echo "unknown")
            
            if (( $(echo "$response_time < 2.0" | bc -l 2>/dev/null || echo 0) )); then
                test_pass "$name responds in ${ms_time}ms (good)"
            elif (( $(echo "$response_time < 5.0" | bc -l 2>/dev/null || echo 0) )); then
                test_pass "$name responds in ${ms_time}ms (acceptable)"
            else
                warning "$name responds in ${ms_time}ms (slow)"
            fi
        else
            test_fail "$name response time test failed"
        fi
    done
}

# Security Headers Test
test_security_headers() {
    log "=== SECURITY HEADERS TESTS ==="
    
    test_start "Security headers on WWW site"
    local www_headers=$(timeout "$TIMEOUT_SHORT" curl -s -I "https://$WWW_HOST/" 2>/dev/null || echo "Connection failed")
    
    local security_headers=("X-Frame-Options" "X-XSS-Protection" "X-Content-Type-Options")
    
    for header in "${security_headers[@]}"; do
        if echo "$www_headers" | grep -qi "$header"; then
            test_pass "$header is present"
        else
            test_fail "$header is missing"
        fi
    done
}

# Comprehensive Test Suite
run_endpoint_tests() {
    test_dns_resolution
    test_ssl_certificates
    test_internal_endpoints
    test_external_website
    test_api_health
    test_chatgpt_schema
    test_api_functionality
    test_security_headers
    test_response_times
}

run_sse_tests() {
    test_sse_endpoint
}

# Test Summary
show_test_summary() {
    echo ""
    echo "=============================================="
    echo "              TEST SUMMARY"
    echo "=============================================="
    echo ""
    echo -e "Total Tests:  ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    echo ""
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        success "All tests passed! ✅"
        echo ""
        echo "🎉 Production infrastructure is working correctly!"
        echo ""
        echo "Verified functionality:"
        echo "  ✓ DNS resolution for all domains"
        echo "  ✓ SSL certificates valid"
        echo "  ✓ Website accessibility" 
        echo "  ✓ API endpoints responding"
        echo "  ✓ ChatGPT Actions schema available"
        echo "  ✓ CORS headers configured"
        echo "  ✓ Security headers present"
        echo "  ✓ Response times acceptable"
        
        return 0
    else
        error "Some tests failed! ❌"
        echo ""
        echo "Issues found:"
        echo "  • $FAILED_TESTS test(s) failed"
        echo "  • Check logs above for details"
        echo "  • Review configuration and retry"
        
        return 1
    fi
}

# Main execution
main() {
    echo "=============================================="
    echo "       PRODUCTION INFRASTRUCTURE SMOKE TESTS"
    echo "=============================================="
    echo ""
    
    case "${1:-}" in
        --verbose)
            set -x
            run_endpoint_tests
            run_sse_tests
            ;;
        --endpoint-only)
            run_endpoint_tests
            ;;
        --sse-test)
            run_sse_tests
            ;;
        --help|-h)
            echo "Usage: $0 [--verbose] [--endpoint-only] [--sse-test]"
            echo ""
            echo "Options:"
            echo "  --verbose       Enable verbose output"
            echo "  --endpoint-only Run only endpoint tests (skip SSE)"
            echo "  --sse-test      Run only SSE tests"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            run_endpoint_tests
            run_sse_tests
            ;;
    esac
    
    show_test_summary
}

# Error handling
trap 'error "Test interrupted"; exit 1' INT TERM

# Execute main function
main "$@"
#!/bin/bash
# RAG++ Memory Service Startup Test

echo "🧪 Testing RAG++ Memory Service Startup"
echo "========================================"

# Check if service is running
echo "📋 Checking service status..."

# Test systemd service
if systemctl --user is-active --quiet ragpp-memory-service.service; then
    echo "✅ Systemd service is running"
else
    echo "❌ Systemd service is not running"
    echo "   Try: systemctl --user start ragpp-memory-service.service"
fi

# Test web API
echo "🌐 Testing web API..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo "✅ Web API is responding"
else
    echo "❌ Web API is not responding"
    echo "   Try: curl http://localhost:8000/health"
fi

# Test memory service
echo "🧠 Testing memory service..."
python3 -c "
try:
    import sys
    sys.path.append('/home/agourakis82/workspace/pcs-meta-repo/ragpp')
    from extended_memory_service import get_memory_service
    memory = get_memory_service()
    stats = memory.get_stats()
    print(f'✅ Memory service operational: {stats["total_memories"]} memories')
except Exception as e:
    print(f'❌ Memory service error: {e}')
"

echo ""
echo "🎯 Service URLs:"
echo "   - Health Check: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Remote Access: http://179.125.169.148:8000"
echo ""
echo "🔧 Management Commands:"
echo "   - Start: systemctl --user start ragpp-memory-service.service"
echo "   - Stop: systemctl --user stop ragpp-memory-service.service"
echo "   - Status: systemctl --user status ragpp-memory-service.service"
echo "   - Logs: journalctl --user -u ragpp-memory-service.service -f"

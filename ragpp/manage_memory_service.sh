#!/bin/bash
# Start RAG++ Memory Service Directly

echo "🚀 Starting RAG++ Extended Memory Service..."

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, chromadb, sentence_transformers" 2>/dev/null || {
    echo "⚠️  Installing missing dependencies..."
    pip install --user fastapi uvicorn chromadb sentence-transformers
}

# Create logs directory
mkdir -p /home/agourakis82/workspace/pcs-meta-repo/ragpp/logs

# Function to start the server
start_server() {
    cd /home/agourakis82/workspace/pcs-meta-repo/ragpp
    
    # Kill any existing process
    pkill -f "python3.*memory_server.py" 2>/dev/null || true
    
    # Start in background
    nohup python3 memory_server.py > logs/memory_server.log 2>&1 &
    SERVER_PID=$!
    
    echo "🌐 Server starting with PID: $SERVER_PID"
    
    # Wait a moment for startup
    sleep 3
    
    # Test if it's working
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ RAG++ Memory Service is running!"
        echo "📍 Local: http://localhost:8000"
        echo "📍 Remote: http://179.125.169.148:8000"
        echo "📖 Docs: http://localhost:8000/docs"
        echo "🧠 Memory API: http://localhost:8000/memory/"
        echo ""
        echo "📋 PID: $SERVER_PID"
        echo "📄 Logs: tail -f $(pwd)/logs/memory_server.log"
        
        # Save PID for management
        echo $SERVER_PID > /tmp/ragpp_memory_service.pid
        
        return 0
    else
        echo "❌ Service failed to start. Check logs:"
        echo "📄 tail -f $(pwd)/logs/memory_server.log"
        return 1
    fi
}

# Function to stop the server
stop_server() {
    if [ -f /tmp/ragpp_memory_service.pid ]; then
        PID=$(cat /tmp/ragpp_memory_service.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "🛑 Stopping RAG++ Memory Service (PID: $PID)..."
            kill $PID
            rm -f /tmp/ragpp_memory_service.pid
            echo "✅ Service stopped"
        else
            echo "⚠️ Service not running"
            rm -f /tmp/ragpp_memory_service.pid
        fi
    else
        echo "⚠️ No PID file found. Killing by process name..."
        pkill -f "python3.*memory_server.py" && echo "✅ Service stopped" || echo "⚠️ No service found"
    fi
}

# Function to check status
check_status() {
    if [ -f /tmp/ragpp_memory_service.pid ]; then
        PID=$(cat /tmp/ragpp_memory_service.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "✅ RAG++ Memory Service is running (PID: $PID)"
            curl -s http://localhost:8000/health > /dev/null && echo "🌐 Web API is responding" || echo "❌ Web API not responding"
        else
            echo "❌ Service not running (stale PID file)"
            rm -f /tmp/ragpp_memory_service.pid
        fi
    else
        echo "❌ Service not running"
    fi
}

# Handle command line arguments
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        start_server
        ;;
    status)
        check_status
        ;;
    logs)
        cd /home/agourakis82/workspace/pcs-meta-repo/ragpp
        echo "📄 Showing memory service logs (Ctrl+C to exit):"
        tail -f logs/memory_server.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the memory service"
        echo "  stop    - Stop the memory service"
        echo "  restart - Restart the memory service"
        echo "  status  - Check service status"
        echo "  logs    - View service logs"
        exit 1
        ;;
esac

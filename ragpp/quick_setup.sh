#!/bin/bash
# Quick Setup Script for RAG++ Extended Memory Auto-Start

echo "🚀 RAG++ Extended Memory - Quick Setup"
echo "====================================="

# Check if we're in the right directory
if [ ! -d "/home/agourakis82/workspace/pcs-meta-repo/ragpp" ]; then
    echo "❌ Error: Please run from the correct directory"
    echo "Expected: /home/agourakis82/workspace/pcs-meta-repo"
    exit 1
fi

cd /home/agourakis82/workspace/pcs-meta-repo/ragpp

echo "📦 Installing dependencies..."
pip install --user sentence-transformers chromadb fastapi uvicorn

echo "🔧 Setting up auto-start configuration..."
python3 setup_autostart.py

echo ""
echo "✅ Setup complete! Your RAG++ Extended Memory is configured."
echo ""
echo "🎯 Quick Commands:"
echo "  Start now:   systemctl --user start ragpp-memory-service"
echo "  Check status: systemctl --user status ragpp-memory-service"
echo "  View logs:   journalctl --user -u ragpp-memory-service -f"
echo "  Test setup:  ./test_startup.sh"
echo ""
echo "🌐 Access URLs:"
echo "  Local:  http://localhost:8000"
echo "  Remote: http://179.125.169.148:8000"
echo "  Docs:   http://179.125.169.148:8000/docs"
echo ""
echo "💡 Your extended memory will start automatically on boot!"

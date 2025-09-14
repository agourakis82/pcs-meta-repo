#!/usr/bin/env bash
"""
Quick Railway Deployment Script
Deploy RAG++ to Railway with HTTPS automatically.
"""

set -e

echo "🚂 RAG++ Railway Deployment"
echo "============================"

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already)
echo "🔐 Checking Railway authentication..."
if ! railway status &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Create new project
echo "📋 Creating Railway project..."
railway_output=$(railway create --name "ragpp-research-api" 2>&1 || true)
echo "$railway_output"

# Get the deployed URL
if [[ $railway_output == *"railway.app"* ]]; then
    RAILWAY_URL=$(echo "$railway_output" | grep -o 'https://[^.]*\.railway\.app' | head -1)
    echo "🌐 Railway URL: $RAILWAY_URL"
else
    echo "⚠️  Could not extract Railway URL. You'll need to set it manually."
    RAILWAY_URL="https://your-app.railway.app"
fi

# Set environment variables
echo "🔧 Setting environment variables..."
API_TOKEN=$(openssl rand -hex 32)
railway env set RAG_API_TOKEN="$API_TOKEN"
railway env set RAG_SERVER_URL="$RAILWAY_URL"
railway env set RAG_HOST="0.0.0.0"
railway env set RAG_PORT="$PORT"

# Create railway.json config
cat > railway.json << EOF
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "python ragpp/ragpp_web_server.py --port \$PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30
  }
}
EOF

# Create Procfile for Railway
cat > Procfile << EOF
web: python ragpp/ragpp_web_server.py --port \$PORT
EOF

# Update requirements for deployment
cat > requirements-railway.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
chromadb==0.4.18
numpy==1.24.3
python-dotenv==1.0.0
EOF

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway deploy

# Get the final URL
FINAL_URL=$(railway status --json | grep -o '"url":"[^"]*' | cut -d'"' -f4 2>/dev/null || echo "$RAILWAY_URL")

echo ""
echo "🎉 Deployment Complete!"
echo "========================"
echo "🌐 Your RAG++ API is live at: $FINAL_URL"
echo "🔑 API Token: $API_TOKEN"
echo ""
echo "📋 Next Steps:"
echo "1. Test your API: curl $FINAL_URL/health"
echo "2. Update ChatGPT Action URL to: $FINAL_URL"
echo "3. Use this token in ChatGPT: $API_TOKEN"
echo ""
echo "📖 API Endpoints:"
echo "  - Health: $FINAL_URL/health"
echo "  - Search: $FINAL_URL/search (POST)"
echo "  - Recent: $FINAL_URL/research/recent (GET)"
echo "  - Docs: $FINAL_URL/docs"
echo ""
echo "🤖 For ChatGPT Custom Actions:"
echo "  - Schema URL: $FINAL_URL/actions/schema"
echo "  - Authentication: Bearer $API_TOKEN"

# Save config for later use
cat > .railway-config << EOF
RAILWAY_URL=$FINAL_URL
API_TOKEN=$API_TOKEN
EOF

echo ""
echo "💾 Configuration saved to .railway-config"
echo "🔐 Keep your API token secure!"

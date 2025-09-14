# RAG++ HTTPS Deployment Guide

## Quick Start (Local Development)

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn python-multipart pydantic
   ```

2. **Set environment variables:**
   ```bash
   export RAG_API_TOKEN="your-generated-token"
   export RAG_SERVER_URL="https://your-domain.com"
   ```

3. **Run server:**
   ```bash
   python ragpp/ragpp_web_server.py
   ```

4. **Test API:**
   ```bash
   curl -X POST "http://localhost:8000/search" \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning psychiatry"}'
   ```

## Production Deployment Options

### Option 1: Railway (Recommended - Free HTTPS)

1. **Create Railway account:** https://railway.app
2. **Deploy from GitHub:**
   - Connect your repository
   - Set environment variables in Railway dashboard
   - Railway provides automatic HTTPS

3. **Environment variables to set:**
   - `RAG_API_TOKEN`: Your generated token
   - `RAG_SERVER_URL`: Your Railway URL (e.g., https://your-app.railway.app)

### Option 2: Heroku

1. **Create Heroku app:**
   ```bash
   heroku create your-ragpp-app
   ```

2. **Set environment variables:**
   ```bash
   heroku config:set RAG_API_TOKEN=your-token
   heroku config:set RAG_SERVER_URL=https://your-ragpp-app.herokuapp.com
   ```

3. **Create Procfile:**
   ```
   web: python ragpp/ragpp_web_server.py --port $PORT
   ```

### Option 3: Render

1. **Create Render account:** https://render.com
2. **Create Web Service from GitHub**
3. **Set build command:** `pip install -r requirements-web.txt`
4. **Set start command:** `python ragpp/ragpp_web_server.py`

### Option 4: Docker + VPS

1. **Build and run:**
   ```bash
   docker-compose up -d
   ```

2. **Configure SSL certificates** (Let's Encrypt recommended)

## ChatGPT Integration

### Method 1: Custom Actions (Recommended)

1. **In ChatGPT:** Go to Settings > Actions
2. **Create new action** with these details:
   - **Authentication:** API Key
   - **Header:** Authorization
   - **Value:** Bearer YOUR_API_TOKEN
   - **Schema:** Use content from `chatgpt_action_config.json`

### Method 2: Plugin (if available)

1. **Upload plugin manifest** to `/.well-known/ai-plugin.json`
2. **Submit to OpenAI** plugin store

## Testing the Integration

1. **Test API endpoints:**
   ```bash
   # Health check
   curl https://your-domain.com/health
   
   # Search test
   curl -X POST "https://your-domain.com/search" \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"query": "recent psychiatric research"}'
   ```

2. **Test in ChatGPT:**
   - Ask: "Search for recent machine learning research in psychiatry"
   - The action should be triggered automatically

## Security Considerations

1. **API Token:** Keep your token secure, rotate regularly
2. **CORS:** Configured for ChatGPT domains only
3. **Rate Limiting:** Consider adding rate limiting for production
4. **HTTPS:** Always use HTTPS in production

## Monitoring

- **API Documentation:** https://your-domain.com/docs
- **Health Check:** https://your-domain.com/health
- **Logs:** Check your deployment platform logs

## Troubleshooting

1. **CORS Issues:** Ensure your domain is in CORS allowlist
2. **Authentication:** Verify API token in Authorization header
3. **SSL Issues:** Ensure proper HTTPS certificate
4. **RAG System:** Check if RAG++ system initializes properly

## Example Usage in ChatGPT

Once configured, you can ask ChatGPT:
- "What are the latest findings in computational psychiatry?"
- "Search for recent research on digital phenotyping"
- "Find studies about machine learning in mental health"

The system will automatically use your RAG++ knowledge base!

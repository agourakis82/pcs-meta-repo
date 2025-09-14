#!/usr/bin/env python3
"""
RAG++ HTTPS Deployment Setup
Configure and deploy RAG++ server for ChatGPT web access.
"""

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path


def generate_api_token():
    """Generate secure API token."""
    return secrets.token_urlsafe(32)


def create_env_file():
    """Create environment configuration file."""
    env_content = f"""# RAG++ Web Server Configuration
RAG_API_TOKEN={generate_api_token()}
RAG_HOST=0.0.0.0
RAG_PORT=8000
RAG_SERVER_URL=https://your-domain.com

# SSL Configuration (for production)
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Optional: Database for logging
LOG_LEVEL=INFO
"""

    env_path = Path(".env")
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"📄 Created environment file: {env_path}")
    print(f"🔑 API Token generated (save this): {env_content.split('=')[1].split()[0]}")
    return env_path


def create_docker_setup():
    """Create Docker configuration for deployment."""

    # Dockerfile
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application
COPY ragpp/ ./ragpp/
COPY pcs/ ./pcs/

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "ragpp/ragpp_web_server.py"]
"""

    # Requirements file
    requirements_content = """fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
chromadb==0.4.18
numpy==1.24.3
"""

    # Docker Compose for production
    docker_compose_content = """version: '3.8'

services:
  ragpp-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - RAG_API_TOKEN=${RAG_API_TOKEN}
      - RAG_SERVER_URL=${RAG_SERVER_URL}
    volumes:
      - ./ragpp/index:/app/ragpp/index
      - ./pcs:/app/pcs
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - ragpp-api
    restart: unless-stopped
"""

    # Nginx configuration
    nginx_conf = """events {
    worker_connections 1024;
}

http {
    upstream ragpp {
        server ragpp-api:8000;
    }
    
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl;
        server_name your-domain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        location / {
            proxy_pass http://ragpp;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # CORS headers for ChatGPT
        add_header Access-Control-Allow-Origin "https://chat.openai.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
    }
}
"""

    # Write files
    files = {
        "Dockerfile": dockerfile_content,
        "requirements-web.txt": requirements_content,
        "docker-compose.yml": docker_compose_content,
        "nginx.conf": nginx_conf,
    }

    for filename, content in files.items():
        with open(filename, "w") as f:
            f.write(content)
        print(f"📄 Created: {filename}")

    return files.keys()


def install_dependencies():
    """Install required Python packages."""
    packages = ["fastapi", "uvicorn[standard]", "python-multipart", "pydantic"]

    print("📦 Installing web server dependencies...")
    for package in packages:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
            )
            print(f"✅ Installed: {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False

    return True


def create_chatgpt_action_config():
    """Create configuration for ChatGPT Custom Actions."""

    action_config = {
        "name": "RAG++ Research Assistant",
        "description": "Access recent scientific literature and research insights",
        "authentication": {
            "type": "API Key",
            "header_name": "Authorization",
            "header_value": "Bearer YOUR_API_TOKEN_HERE",
        },
        "schema": {
            "openapi": "3.0.0",
            "info": {"title": "RAG++ Research API", "version": "1.0.0"},
            "servers": [{"url": "https://your-domain.com"}],
            "paths": {
                "/search": {
                    "post": {
                        "operationId": "searchResearch",
                        "summary": "Search research literature",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "Research question",
                                            },
                                            "max_results": {
                                                "type": "integer",
                                                "default": 10,
                                            },
                                        },
                                        "required": ["query"],
                                    }
                                }
                            },
                        },
                    }
                }
            },
        },
    }

    config_path = Path("chatgpt_action_config.json")
    with open(config_path, "w") as f:
        json.dump(action_config, f, indent=2)

    print(f"📄 Created ChatGPT Action config: {config_path}")
    return config_path


def create_deployment_guide():
    """Create deployment guide."""

    guide_content = """# RAG++ HTTPS Deployment Guide

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

### Local HTTPS (self-signed, dev only)

```bash
# Generate dev certs
tools/generate_self_signed_cert.sh

# Ensure .env has SSL_CERT_PATH/SSL_KEY_PATH pointing to ssl/dev_*.pem
tools/run_ragpp_https.sh
```

4. **Test API:**
   ```bash
   curl -X POST "http://localhost:8000/search" \\
     -H "Authorization: Bearer your-token" \\
     -H "Content-Type: application/json" \\
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
   curl -X POST "https://your-domain.com/search" \\
     -H "Authorization: Bearer your-token" \\
     -H "Content-Type: application/json" \\
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
"""

    guide_path = Path("deployment_guide.md")
    with open(guide_path, "w") as f:
        f.write(guide_content)

    print(f"📖 Created deployment guide: {guide_path}")
    return guide_path


def main():
    """Main setup function."""
    print("🌐 RAG++ HTTPS Deployment Setup")
    print("=" * 40)

    # Create directory structure
    os.makedirs("ssl", exist_ok=True)

    # Step 1: Install dependencies
    print("\n📦 Step 1: Installing dependencies...")
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return

    # Step 2: Create environment configuration
    print("\n🔧 Step 2: Creating environment configuration...")
    env_file = create_env_file()

    # Step 3: Create Docker setup
    print("\n🐳 Step 3: Creating Docker configuration...")
    docker_files = create_docker_setup()

    # Step 4: Create ChatGPT action config
    print("\n🤖 Step 4: Creating ChatGPT configuration...")
    action_config = create_chatgpt_action_config()

    # Step 5: Create deployment guide
    print("\n📖 Step 5: Creating deployment guide...")
    guide = create_deployment_guide()

    print("\n🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Choose a deployment platform (Railway, Heroku, Render)")
    print("2. Set your domain in environment variables")
    print("3. Deploy your application")
    print("4. Configure ChatGPT Custom Action")
    print("5. Test the integration!")

    print(f"\n📁 Files created:")
    print(f"  - {env_file}")
    print(f"  - {action_config}")
    print(f"  - {guide}")
    for file in docker_files:
        print(f"  - {file}")

    print(f"\n🔑 Important: Save your API token from {env_file}")
    print("📖 Read deployment_guide.md for detailed instructions")


if __name__ == "__main__":
    main()
    main()

#!/usr/bin/env python3
"""
Auto-Start Service for RAG++ Extended Memory
Configura o sistema para iniciar automaticamente com o computador.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any

class AutoStartService:
    """
    Serviço para configurar auto-inicialização do RAG++ Extended Memory.
    """
    
    def __init__(self, project_dir: str = "/home/agourakis82/workspace/pcs-meta-repo"):
        self.project_dir = Path(project_dir)
        self.ragpp_dir = self.project_dir / "ragpp"
        self.service_name = "ragpp-memory-service"
        
        # User directories
        self.user = os.getenv('USER', 'agourakis82')
        self.home_dir = Path.home()
        
        # Service paths
        self.systemd_user_dir = self.home_dir / ".config/systemd/user"
        self.autostart_dir = self.home_dir / ".config/autostart"
        
    def create_systemd_service(self) -> str:
        """
        Cria serviço systemd para auto-inicialização.
        
        Returns:
            Caminho do arquivo de serviço criado
        """
        # Create systemd user directory
        self.systemd_user_dir.mkdir(parents=True, exist_ok=True)
        
        # Service configuration
        service_content = f"""[Unit]
Description=RAG++ Extended Memory Service
After=network.target
Wants=network.target

[Service]
Type=simple
User={self.user}
WorkingDirectory={self.ragpp_dir}
Environment=HOME={self.home_dir}
Environment=PATH=/usr/local/bin:/usr/bin:/bin:{self.home_dir}/.local/bin
ExecStart=/usr/bin/python3 {self.ragpp_dir}/memory_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""
        
        # Write service file
        service_path = self.systemd_user_dir / f"{self.service_name}.service"
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Systemd service created: {service_path}")
        return str(service_path)
    
    def create_desktop_autostart(self) -> str:
        """
        Cria entrada de autostart no desktop.
        
        Returns:
            Caminho do arquivo .desktop criado
        """
        # Create autostart directory
        self.autostart_dir.mkdir(parents=True, exist_ok=True)
        
        # Desktop entry configuration
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=RAG++ Memory Service
Comment=Extended Memory Service for ChatGPT Integration
Icon=applications-internet
Exec=/usr/bin/python3 {self.ragpp_dir}/memory_server.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Development;
"""
        
        # Write desktop file
        desktop_path = self.autostart_dir / f"{self.service_name}.desktop"
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
        
        # Make executable
        os.chmod(desktop_path, 0o755)
        
        print(f"✅ Desktop autostart created: {desktop_path}")
        return str(desktop_path)
    
    def create_memory_server_script(self) -> str:
        """
        Cria script principal do servidor de memória.
        
        Returns:
            Caminho do script criado
        """
        server_script = f"""#!/usr/bin/env python3
\"\"\"
RAG++ Memory Server - Auto-Start Script
Servidor principal que combina RAG++, Extended Memory e Web API.
\"\"\"

import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"memory_server_{{datetime.now().strftime('%Y%m%d')}}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import our services
try:
    from extended_memory_service import ExtendedMemoryService, get_memory_service
    from ragpp_web_server import app as web_app
    import uvicorn
except ImportError as e:
    logger.error(f"❌ Import error: {{e}}")
    sys.exit(1)

class MemoryServerManager:
    \"\"\"
    Gerenciador principal do servidor de memória.
    \"\"\"
    
    def __init__(self):
        self.memory_service = None
        self.web_server = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)
    
    async def start_services(self):
        \"\"\"Inicia todos os serviços.\"\"\"
        try:
            logger.info("🚀 Starting RAG++ Memory Server...")
            
            # Initialize memory service
            logger.info("🧠 Initializing Extended Memory Service...")
            self.memory_service = get_memory_service()
            
            # Store startup context
            self.memory_service.store_project_context(
                project_name="pcs-meta-repo",
                context_type="system_startup",
                content=f"RAG++ Memory Server started automatically at {{datetime.now().isoformat()}}. All services operational.",
                metadata={{
                    "startup_time": datetime.now().isoformat(),
                    "auto_start": True,
                    "services": ["memory", "web_api", "rag++"]
                }}
            )
            
            logger.info("✅ Extended Memory Service initialized")
            
            # Start web server
            logger.info("🌐 Starting Web API Server...")
            self.running = True
            
            # Run web server
            config = uvicorn.Config(
                web_app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                access_log=True
            )
            server = uvicorn.Server(config)
            
            logger.info("✅ RAG++ Memory Server fully operational!")
            logger.info("🔗 Access at: http://179.125.169.148:8000")
            logger.info("📚 API docs: http://179.125.169.148:8000/docs")
            
            await server.serve()
            
        except Exception as e:
            logger.error(f"❌ Error starting services: {{e}}")
            sys.exit(1)
    
    def shutdown_handler(self, signum, frame):
        \"\"\"Handle graceful shutdown.\"\"\"
        logger.info(f"📤 Received signal {{signum}}, shutting down gracefully...")
        
        if self.memory_service:
            # Store shutdown context
            self.memory_service.store_project_context(
                project_name="pcs-meta-repo",
                context_type="system_shutdown",
                content=f"RAG++ Memory Server shutdown gracefully at {{datetime.now().isoformat()}}.",
                metadata={{
                    "shutdown_time": datetime.now().isoformat(),
                    "signal": signum,
                    "graceful": True
                }}
            )
            
            # Create backup before shutdown
            backup_path = self.memory_service.create_backup()
            logger.info(f"💾 Final backup created: {{backup_path}}")
        
        self.running = False
        logger.info("✅ RAG++ Memory Server shutdown complete")
        sys.exit(0)

async def main():
    \"\"\"Main entry point.\"\"\"
    manager = MemoryServerManager()
    await manager.start_services()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {{e}}")
        sys.exit(1)
"""
        
        # Write server script
        script_path = self.ragpp_dir / "memory_server.py"
        with open(script_path, 'w') as f:
            f.write(server_script)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        print(f"✅ Memory server script created: {script_path}")
        return str(script_path)
    
    def setup_autostart(self) -> Dict[str, Any]:
        """
        Configura auto-inicialização completa.
        
        Returns:
            Dicionário com informações de configuração
        """
        results = {}
        
        try:
            # Create memory server script
            script_path = self.create_memory_server_script()
            results['server_script'] = script_path
            
            # Create systemd service
            service_path = self.create_systemd_service()
            results['systemd_service'] = service_path
            
            # Create desktop autostart
            desktop_path = self.create_desktop_autostart()
            results['desktop_autostart'] = desktop_path
            
            # Enable and start systemd service
            try:
                # Reload systemd daemon
                subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
                
                # Enable service
                subprocess.run(['systemctl', '--user', 'enable', f'{self.service_name}.service'], check=True)
                
                print(f"✅ Systemd service enabled for auto-start")
                results['systemd_enabled'] = True
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Warning: Could not enable systemd service: {e}")
                results['systemd_enabled'] = False
            
            # Create startup test script
            test_script = self.create_startup_test_script()
            results['test_script'] = test_script
            
            return results
            
        except Exception as e:
            print(f"❌ Error setting up autostart: {e}")
            return {'error': str(e)}
    
    def create_startup_test_script(self) -> str:
        """
        Cria script para testar a inicialização.
        
        Returns:
            Caminho do script de teste
        """
        test_script = f"""#!/bin/bash
# RAG++ Memory Service Startup Test

echo "🧪 Testing RAG++ Memory Service Startup"
echo "========================================"

# Check if service is running
echo "📋 Checking service status..."

# Test systemd service
if systemctl --user is-active --quiet {self.service_name}.service; then
    echo "✅ Systemd service is running"
else
    echo "❌ Systemd service is not running"
    echo "   Try: systemctl --user start {self.service_name}.service"
fi

# Test web API
echo "🌐 Testing web API..."
if curl -s -o /dev/null -w "%{{http_code}}" http://localhost:8000/health | grep -q "200"; then
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
    sys.path.append('{self.ragpp_dir}')
    from extended_memory_service import get_memory_service
    memory = get_memory_service()
    stats = memory.get_stats()
    print(f'✅ Memory service operational: {{stats[\"total_memories\"]}} memories')
except Exception as e:
    print(f'❌ Memory service error: {{e}}')
"

echo ""
echo "🎯 Service URLs:"
echo "   - Health Check: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Remote Access: http://179.125.169.148:8000"
echo ""
echo "🔧 Management Commands:"
echo "   - Start: systemctl --user start {self.service_name}.service"
echo "   - Stop: systemctl --user stop {self.service_name}.service"
echo "   - Status: systemctl --user status {self.service_name}.service"
echo "   - Logs: journalctl --user -u {self.service_name}.service -f"
"""
        
        # Write test script
        test_path = self.ragpp_dir / "test_startup.sh"
        with open(test_path, 'w') as f:
            f.write(test_script)
        
        # Make executable
        os.chmod(test_path, 0o755)
        
        print(f"✅ Startup test script created: {test_path}")
        return str(test_path)
    
    def start_service_now(self):
        """Inicia o serviço imediatamente."""
        try:
            # Start systemd service
            subprocess.run(['systemctl', '--user', 'start', f'{self.service_name}.service'], check=True)
            print(f"✅ Service started: {self.service_name}")
            
            # Show status
            result = subprocess.run(
                ['systemctl', '--user', 'status', f'{self.service_name}.service', '--no-pager'],
                capture_output=True, text=True
            )
            print("📊 Service Status:")
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error starting service: {e}")
    
    def create_memory_management_api(self) -> str:
        """
        Cria endpoints de API para gerenciamento de memória.
        
        Returns:
            Caminho do arquivo de endpoints
        """
        endpoints_script = f"""#!/usr/bin/env python3
\"\"\"
Memory Management API Endpoints
Endpoints adicionais para gerenciamento da memória extendida.
\"\"\"

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from extended_memory_service import get_memory_service

# Create router
memory_router = APIRouter(prefix="/memory", tags=["memory"])

# Request models
class StoreMemoryRequest(BaseModel):
    content: str
    memory_type: str = "general"
    tags: List[str] = []
    metadata: Dict[str, Any] = {{}}
    importance_score: float = 0.5

class StoreConversationRequest(BaseModel):
    conversation_data: Dict[str, Any]
    title: Optional[str] = None
    importance_score: float = 0.5

class StoreProjectContextRequest(BaseModel):
    project_name: str = "pcs-meta-repo"
    context_type: str
    content: str
    metadata: Dict[str, Any] = {{}}

class SearchMemoryRequest(BaseModel):
    query: str
    memory_types: Optional[List[str]] = None
    max_results: int = 10
    importance_threshold: float = 0.3

# Memory service dependency
def get_memory():
    return get_memory_service()

@memory_router.post("/store")
async def store_memory(request: StoreMemoryRequest, memory_service = Depends(get_memory)):
    \"\"\"Armazena uma nova memória.\"\"\"
    try:
        memory_id = memory_service.store_memory(
            content=request.content,
            memory_type=request.memory_type,
            tags=request.tags,
            metadata=request.metadata,
            importance_score=request.importance_score
        )
        return {{"memory_id": memory_id, "status": "stored"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/store/conversation")
async def store_conversation(request: StoreConversationRequest, memory_service = Depends(get_memory)):
    \"\"\"Armazena uma conversa completa.\"\"\"
    try:
        conv_id = memory_service.store_conversation(
            conversation_data=request.conversation_data,
            title=request.title,
            importance_score=request.importance_score
        )
        return {{"conversation_id": conv_id, "status": "stored"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/store/project")
async def store_project_context(request: StoreProjectContextRequest, memory_service = Depends(get_memory)):
    \"\"\"Armazena contexto do projeto.\"\"\"
    try:
        context_id = memory_service.store_project_context(
            project_name=request.project_name,
            context_type=request.context_type,
            content=request.content,
            metadata=request.metadata
        )
        return {{"context_id": context_id, "status": "stored"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/search")
async def search_memory(request: SearchMemoryRequest, memory_service = Depends(get_memory)):
    \"\"\"Busca na memória usando busca semântica.\"\"\"
    try:
        results = memory_service.search_memory(
            query=request.query,
            memory_types=request.memory_types,
            max_results=request.max_results,
            importance_threshold=request.importance_threshold
        )
        return {{"query": request.query, "results": results, "count": len(results)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/recent")
async def get_recent_memories(
    days: int = 7,
    memory_types: Optional[str] = None,
    max_results: int = 20,
    memory_service = Depends(get_memory)
):
    \"\"\"Recupera memórias recentes.\"\"\"
    try:
        types_list = memory_types.split(',') if memory_types else None
        results = memory_service.get_recent_memories(
            days=days,
            memory_types=types_list,
            max_results=max_results
        )
        return {{"recent_memories": results, "count": len(results), "days": days}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/project/status")
async def get_project_status(
    project_name: str = "pcs-meta-repo",
    memory_service = Depends(get_memory)
):
    \"\"\"Recupera status do projeto.\"\"\"
    try:
        status = memory_service.get_project_status(project_name)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/stats")
async def get_memory_stats(memory_service = Depends(get_memory)):
    \"\"\"Estatísticas do serviço de memória.\"\"\"
    try:
        stats = memory_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/backup")
async def create_backup(memory_service = Depends(get_memory)):
    \"\"\"Cria backup da memória.\"\"\"
    try:
        backup_path = memory_service.create_backup()
        return {{"backup_path": backup_path, "timestamp": datetime.now().isoformat()}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.post("/cleanup")
async def cleanup_memories(days_to_keep: int = 90, memory_service = Depends(get_memory)):
    \"\"\"Limpa memórias antigas.\"\"\"
    try:
        deleted_count = memory_service.cleanup_old_memories(days_to_keep)
        return {{"deleted_count": deleted_count, "days_kept": days_to_keep}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ChatGPT integration endpoints
@memory_router.post("/chatgpt/context")
async def store_chatgpt_context(
    conversation_title: str,
    messages: List[Dict[str, str]],
    context_summary: str = "",
    importance_score: float = 0.7,
    memory_service = Depends(get_memory)
):
    \"\"\"Armazena contexto de conversa do ChatGPT.\"\"\"
    try:
        # Store as conversation
        conversation_data = {{
            "messages": messages,
            "summary": context_summary,
            "source": "chatgpt",
            "timestamp": datetime.now().isoformat()
        }}
        
        conv_id = memory_service.store_conversation(
            conversation_data=conversation_data,
            title=conversation_title,
            importance_score=importance_score
        )
        
        # Also store key insights as individual memories
        for i, msg in enumerate(messages):
            if msg.get('role') == 'assistant' and len(msg.get('content', '')) > 100:
                memory_service.store_memory(
                    content=msg['content'],
                    memory_type="chatgpt_insight",
                    tags=["chatgpt", "insight", conversation_title],
                    metadata={{
                        "conversation_id": conv_id,
                        "message_index": i,
                        "source": "chatgpt"
                    }},
                    importance_score=importance_score * 0.8
                )
        
        return {{
            "conversation_id": conv_id,
            "status": "stored",
            "message_count": len(messages)
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@memory_router.get("/chatgpt/recall")
async def recall_context(
    query: str,
    include_conversations: bool = True,
    include_insights: bool = True,
    max_results: int = 10,
    memory_service = Depends(get_memory)
):
    \"\"\"Recupera contexto relevante para o ChatGPT.\"\"\"
    try:
        memory_types = []
        if include_conversations:
            memory_types.extend(["conversation"])
        if include_insights:
            memory_types.extend(["chatgpt_insight", "insight", "context"])
        
        results = memory_service.search_memory(
            query=query,
            memory_types=memory_types if memory_types else None,
            max_results=max_results,
            importance_threshold=0.4
        )
        
        # Format for ChatGPT consumption
        context_summary = []
        for result in results:
            context_summary.append({{
                "content": result['content'][:500] + "..." if len(result['content']) > 500 else result['content'],
                "type": result['memory_type'],
                "relevance": result['relevance_score'],
                "timestamp": result['timestamp'],
                "tags": result['tags']
            }})
        
        return {{
            "query": query,
            "context": context_summary,
            "total_results": len(results),
            "summary": f"Found {{len(results)}} relevant memories for your query."
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
        
        # Write endpoints script
        endpoints_path = self.ragpp_dir / "memory_api_endpoints.py"
        with open(endpoints_path, 'w') as f:
            f.write(endpoints_script)
        
        print(f"✅ Memory management API created: {endpoints_path}")
        return str(endpoints_path)

def main():
    """Main setup function."""
    print("🚀 Setting up RAG++ Extended Memory Auto-Start")
    print("=" * 50)
    
    autostart = AutoStartService()
    
    # Create memory management API
    api_path = autostart.create_memory_management_api()
    print(f"📡 Memory API endpoints: {api_path}")
    
    # Setup auto-start
    results = autostart.setup_autostart()
    
    print("\n✅ Auto-Start Configuration Complete!")
    print("=" * 50)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print("📁 Files Created:")
    for key, path in results.items():
        if key != 'systemd_enabled':
            print(f"  - {key}: {path}")
    
    print(f"\n🔧 Systemd Service: {'✅ Enabled' if results.get('systemd_enabled') else '❌ Not enabled'}")
    
    print("\n🎯 Quick Start:")
    print("1. Start service now: systemctl --user start ragpp-memory-service")
    print("2. Check status: systemctl --user status ragpp-memory-service")
    print("3. View logs: journalctl --user -u ragpp-memory-service -f")
    print("4. Test startup: ./test_startup.sh")
    
    print("\n🌐 Your Extended Memory will be available at:")
    print("  - Local: http://localhost:8000")
    print("  - Remote: http://179.125.169.148:8000")
    print("  - API Docs: http://179.125.169.148:8000/docs")
    print("  - Memory API: http://179.125.169.148:8000/memory/")
    
    print("\n💡 Usage Examples:")
    print("  - Store memory: POST /memory/store")
    print("  - Search memory: POST /memory/search")
    print("  - ChatGPT context: POST /memory/chatgpt/context")
    print("  - Recall context: GET /memory/chatgpt/recall?query=...")
    
    # Ask if user wants to start now
    start_now = input("\n🚀 Start the service now? (y/n): ").lower().strip()
    if start_now in ['y', 'yes', 's', 'sim']:
        autostart.start_service_now()
    
    print("\n🎉 Your Extended Memory is ready! It will start automatically on boot.")

if __name__ == "__main__":
    main()

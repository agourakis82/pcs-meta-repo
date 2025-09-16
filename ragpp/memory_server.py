#!/usr/bin/env python3
"""
RAG++ Memory Server - Auto-Start Script
Servidor principal que combina RAG++, Extended Memory e Web API.
"""

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
        logging.FileHandler(log_dir / f"memory_server_{datetime.now().strftime('%Y%m%d')}.log"),
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
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

class MemoryServerManager:
    """
    Gerenciador principal do servidor de memória.
    """
    
    def __init__(self):
        self.memory_service = None
        self.web_server = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)
    
    async def start_services(self):
        """Inicia todos os serviços."""
        try:
            logger.info("🚀 Starting RAG++ Memory Server...")
            
            # Initialize memory service
            logger.info("🧠 Initializing Extended Memory Service...")
            self.memory_service = get_memory_service()
            
            # Store startup context
            self.memory_service.store_project_context(
                project_name="pcs-meta-repo",
                context_type="system_startup",
                content=f"RAG++ Memory Server started automatically at {datetime.now().isoformat()}. All services operational.",
                metadata={
                    "startup_time": datetime.now().isoformat(),
                    "auto_start": True,
                    "services": ["memory", "web_api", "rag++"]
                }
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
            logger.error(f"❌ Error starting services: {e}")
            sys.exit(1)
    
    def shutdown_handler(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info(f"📤 Received signal {signum}, shutting down gracefully...")
        
        if self.memory_service:
            # Store shutdown context
            self.memory_service.store_project_context(
                project_name="pcs-meta-repo",
                context_type="system_shutdown",
                content=f"RAG++ Memory Server shutdown gracefully at {datetime.now().isoformat()}.",
                metadata={
                    "shutdown_time": datetime.now().isoformat(),
                    "signal": signum,
                    "graceful": True
                }
            )
            
            # Create backup before shutdown
            backup_path = self.memory_service.create_backup()
            logger.info(f"💾 Final backup created: {backup_path}")
        
        self.running = False
        logger.info("✅ RAG++ Memory Server shutdown complete")
        sys.exit(0)

async def main():
    """Main entry point."""
    manager = MemoryServerManager()
    await manager.start_services()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

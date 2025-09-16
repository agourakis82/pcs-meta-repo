#!/usr/bin/env python3
"""
RAG++ Enhanced Research Agent - Main Interface
==============================================

Comprehensive demonstration of the long-horizon reasoning agent
with continuous scientific discovery capabilities.

Usage:
    python rag_plus_main.py --config rag_plus_config.yaml
    python rag_plus_main.py --demo
    python rag_plus_main.py --monitor
    
Author: PCS-Meta-Repo Team
Date: September 2025
"""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml
from loguru import logger

# Import our modules
from rag_plus_agent import RAGConfig, RAGPlusPlusAgent
from scientific_discovery_radar import (
    DEFAULT_SOURCES,
    ScientificDiscoveryRadar,
    SourceConfig,
)


class RAGPlusSystemManager:
    """
    Main system manager for RAG++ Enhanced Research Agent.
    
    Handles configuration, initialization, and orchestration of
    all system components including the RAG engine and discovery radar.
    """
    
    def __init__(self, config_path: str = "rag_plus_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.rag_agent = None
        self.discovery_radar = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration if file not found"""
        return {
            "gcp": {
                "project_id": os.getenv("GCP_PROJECT_ID", "your-gcp-project"),
                "location": "us-central1"
            },
            "bigquery": {
                "dataset_id": "knowledge_base",
                "table_id": "documents"
            },
            "vertex_ai": {
                "embedding_model": "textembedding-gecko@001",
                "generation_model": "text-bison@001"
            },
            "rag": {
                "novelty_threshold": 0.8,
                "max_iterations": 10,
                "top_k_retrieval": 5
            },
            "monitoring": {
                "continuous_enabled": False,
                "check_interval": 3600,
                "log_level": "INFO"
            }
        }
    
    def initialize_system(self) -> bool:
        """Initialize RAG agent and discovery radar"""
        try:
            # Create RAG configuration
            rag_config = RAGConfig(
                project_id=self.config["gcp"]["project_id"],
                location=self.config["gcp"]["location"],
                dataset_id=self.config["bigquery"]["dataset_id"],
                table_id=self.config["bigquery"]["table_id"],
                embedding_model=self.config["vertex_ai"]["embedding_model"],
                generation_model=self.config["vertex_ai"]["generation_model"],
                novelty_threshold=self.config["rag"]["novelty_threshold"],
                max_iterations=self.config["rag"]["max_iterations"],
                top_k_retrieval=self.config["rag"]["top_k_retrieval"]
            )
            
            # Initialize RAG agent
            logger.info("Initializing RAG++ Agent...")
            self.rag_agent = RAGPlusPlusAgent(rag_config)
            
            # Parse sources configuration
            sources = []
            if "sources" in self.config:
                for src_config in self.config["sources"]:
                    source = SourceConfig(
                        name=src_config["name"],
                        type=src_config["type"],
                        url=src_config["url"],
                        enabled=src_config.get("enabled", True),
                        check_interval=src_config.get("check_interval", 3600)
                    )
                    sources.append(source)
            else:
                sources = DEFAULT_SOURCES
            
            # Initialize discovery radar
            logger.info("Initializing Scientific Discovery Radar...")
            self.discovery_radar = ScientificDiscoveryRadar(self.rag_agent, sources)
            
            logger.info("✅ System initialization complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    def run_demo(self):
        """Run interactive demonstration of the system"""
        print("\n" + "="*60)
        print("🚀 RAG++ Enhanced Research Agent - Demo Mode")
        print("="*60)
        
        if not self.initialize_system():
            print("❌ Failed to initialize system. Check your configuration.")
            return
        
        # Demo questions
        demo_questions = [
            "O que são transformers em deep learning?",
            "Quais são as últimas descobertas em IA generativa?",
            "Compare diferentes abordagens de few-shot learning"
        ]
        
        print("\n📚 Demo: Testing RAG system with sample questions")
        print("-" * 50)
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n🔍 Pergunta {i}: {question}")
            print("-" * 30)
            
            try:
                # Test simple RAG
                print("📄 Resposta Simples:")
                answer = self.rag_agent.answer_question(question)
                print(f"   {answer}\n")
                
                # Test iterative reasoning for complex questions
                if i == 3:  # Use iterative for last question
                    print("🧠 Resposta com Raciocínio Iterativo:")
                    iterative_answer = self.rag_agent.answer_question_iterative(question)
                    print(f"   {iterative_answer}\n")
                    
            except Exception as e:
                print(f"   ❌ Erro: {e}\n")
        
        # Demo discovery radar
        print("\n🔬 Demo: Testing Scientific Discovery Radar")
        print("-" * 50)
        
        try:
            stats = self.discovery_radar.update_knowledge_base_from_feeds()
            print(f"📊 Estatísticas da atualização:")
            print(f"   • Artigos encontrados: {stats['fetched']}")
            print(f"   • Artigos novos: {stats['novel']}")
            print(f"   • Adicionados à base: {stats['added']}")
            print(f"   • Erros: {stats['errors']}")
        except Exception as e:
            print(f"   ❌ Erro no radar: {e}")
        
        print("\n✅ Demo concluída!")
    
    def run_interactive(self):
        """Run interactive question-answering session"""
        print("\n" + "="*60)
        print("💬 RAG++ Enhanced Research Agent - Modo Interativo")
        print("="*60)
        print("Digite suas perguntas (ou 'quit' para sair)")
        print("Comandos especiais:")
        print("  /iterative <pergunta> - Usar raciocínio iterativo")
        print("  /update - Atualizar base de conhecimento")
        print("  /stats - Mostrar estatísticas do sistema")
        print("-" * 60)
        
        if not self.initialize_system():
            print("❌ Falha na inicialização. Verifique sua configuração.")
            return
        
        while True:
            try:
                user_input = input("\n🔍 Pergunta: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    print("👋 Até logo!")
                    break
                
                if user_input.startswith('/iterative '):
                    question = user_input[11:]
                    print("🧠 Processando com raciocínio iterativo...")
                    answer = self.rag_agent.answer_question_iterative(question)
                    print(f"📝 Resposta: {answer}")
                    
                elif user_input == '/update':
                    print("🔄 Atualizando base de conhecimento...")
                    stats = self.discovery_radar.update_knowledge_base_from_feeds()
                    print(f"✅ Atualização completa: {stats['added']} novos itens adicionados")
                    
                elif user_input == '/stats':
                    print("📊 Estatísticas do sistema:")
                    print(f"   • Projeto GCP: {self.config['gcp']['project_id']}")
                    print(f"   • Dataset: {self.config['bigquery']['dataset_id']}")
                    print(f"   • Fontes monitoradas: {len(self.discovery_radar.sources)}")
                    
                elif user_input:
                    print("💭 Processando...")
                    answer = self.rag_agent.answer_question(user_input)
                    print(f"📝 Resposta: {answer}")
                    
            except KeyboardInterrupt:
                print("\n👋 Sessão interrompida. Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    async def run_monitoring(self):
        """Run continuous monitoring mode"""
        print("\n" + "="*60)
        print("📡 RAG++ Enhanced Research Agent - Modo Monitoramento")
        print("="*60)
        
        if not self.initialize_system():
            print("❌ Falha na inicialização. Verifique sua configuração.")
            return
        
        check_interval = self.config["monitoring"]["check_interval"]
        print(f"🔄 Iniciando monitoramento contínuo (intervalo: {check_interval}s)")
        print("Pressione Ctrl+C para parar...")
        
        # Setup signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\n🛑 Parando monitoramento...")
            self.discovery_radar.stop_monitoring()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            await self.discovery_radar.run_continuous_monitoring(check_interval)
        except KeyboardInterrupt:
            print("🛑 Monitoramento parado pelo usuário")
        except Exception as e:
            logger.error(f"Erro no monitoramento: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RAG++ Enhanced Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--config", 
        default="rag_plus_config.yaml",
        help="Configuration file path"
    )
    parser.add_argument(
        "--demo", 
        action="store_true",
        help="Run demonstration mode"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Run interactive Q&A mode"
    )
    parser.add_argument(
        "--monitor", 
        action="store_true",
        help="Run continuous monitoring mode"
    )
    
    args = parser.parse_args()
    
    # Initialize system manager
    system = RAGPlusSystemManager(args.config)
    
    try:
        if args.demo:
            system.run_demo()
        elif args.monitor:
            asyncio.run(system.run_monitoring())
        elif args.interactive:
            system.run_interactive()
        else:
            # Default: show help and run demo
            parser.print_help()
            print("\n🚀 Executando modo demo por padrão...\n")
            system.run_demo()
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()        sys.exit(1)


if __name__ == "__main__":
    main()
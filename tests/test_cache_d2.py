#!/usr/bin/env python3
"""
Teste rápido para verificar funcionalidade do sistema de cache D2.
"""

import asyncio
import sys
import os

# Adicionar o diretório api ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from cache import CacheManager, MemoryCache, get_cache_stats

async def test_cache_system():
    """Teste básico do sistema de cache."""
    print("🔧 Testando Sistema de Cache D2...")
    
    try:
        # Inicializar cache manager
        cache_manager = CacheManager()
        await cache_manager.initialize()
        print("✅ Cache Manager inicializado com sucesso")
        
        # Teste básico de cache
        test_key = "test_key"
        test_value = {"message": "Hello Cache!", "timestamp": "2024-01-01"}
        
        # Armazenar valor
        await cache_manager.set(test_key, test_value, ttl=60)
        print(f"✅ Valor armazenado no cache: {test_key}")
        
        # Recuperar valor
        cached_value = await cache_manager.get(test_key)
        print(f"✅ Valor recuperado do cache: {cached_value}")
        
        # Verificar se valores são iguais
        if cached_value == test_value:
            print("✅ Cache funcionando corretamente!")
        else:
            print("❌ Erro: valor recuperado é diferente do armazenado")
            return False
        
        # Teste de estatísticas
        stats = await get_cache_stats()
        print(f"✅ Estatísticas do cache obtidas: {stats.keys()}")
        
        # Teste de invalidação por tags
        await cache_manager.set("tagged_key", {"data": "tagged"}, ttl=60, tags=["test_tag"])
        from cache import invalidate_cache_tags
        invalidated = await invalidate_cache_tags(["test_tag"])
        print(f"✅ Entries invalidadas por tag: {invalidated}")
        
        # Limpeza
        await cache_manager.shutdown()
        print("✅ Cache Manager finalizado com sucesso")
        
        print("\n🎉 TODOS OS TESTES DE CACHE PASSARAM!")
        print("🚀 Sistema de Cache D2 IMPLEMENTADO COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante teste de cache: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_cache_system())
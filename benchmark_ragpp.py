#!/usr/bin/env python3
"""
Benchmark RAG++ Server Performance
Testa performance de diferentes endpoints.
"""

import time
import requests
import statistics

def benchmark_endpoint(url, method="GET", data=None, iterations=5):
    """Benchmark simples de endpoint."""
    times = []

    for i in range(iterations):
        start = time.time()
        try:
            if method == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            response.raise_for_status()
            elapsed = time.time() - start
            times.append(elapsed)
            print(".3f")
        except Exception as e:
            elapsed = time.time() - start
            print(".3f")

    if times:
        avg_time = statistics.mean(times)
        print(".3f")
        return avg_time
    return None

def main():
    """Benchmark principal."""
    base_url = "http://127.0.0.1:8000"

    print("🚀 Benchmark RAG++ Server")
    print("=" * 40)

    # Testes básicos
    endpoints = [
        ("/health", "GET"),
        ("/test", "GET"),
    ]

    results = {}

    for endpoint, method in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n🔬 Testando {method} {endpoint}")
        avg_time = benchmark_endpoint(url, method)
        if avg_time:
            results[endpoint] = avg_time

    # Teste de busca
    search_data = {
        "query": "machine learning in psychiatry",
        "max_results": 3,
        "search_type": "literature"
    }

    print("
🔬 Testando busca literatura"    avg_search = benchmark_endpoint(f"{base_url}/search", "POST", search_data)
    if avg_search:
        results["/search"] = avg_search

    # Resumo
    print("\n" + "=" * 40)
    print("📊 RESULTADOS FINAIS")
    print("=" * 40)

    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1])
        print("🏆 Ranking (mais rápido primeiro):")
        for i, (endpoint, avg_time) in enumerate(sorted_results, 1):
            print(f"  {i}. {endpoint}: {avg_time:.3f}s")
    else:
        print("❌ Nenhum teste teve sucesso")

if __name__ == "__main__":
    main()

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
import requests
import statistics

class RAGBenchmark:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def time_request(self, endpoint, method="GET", data=None, headers=None):
        """Mede tempo de uma requisição."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            if method == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=30)
            else:
                response = self.session.get(url, headers=headers, timeout=30)

            response.raise_for_status()
            elapsed = time.time() - start_time
            return elapsed, response.status_code
        except Exception as e:
            elapsed = time.time() - start_time
            return elapsed, str(e)

    def benchmark_endpoint(self, endpoint, method="GET", data=None, headers=None, iterations=10):
        """Benchmark de um endpoint específico."""
        print(f"\n🔬 Testando {method} {endpoint} ({iterations} iterações)")

        times = []
        errors = 0

        for i in range(iterations):
            elapsed, status = self.time_request(endpoint, method, data, headers)
            times.append(elapsed)

            if isinstance(status, str):  # Error
                errors += 1
                print(f"  ❌ Iteração {i+1}: {status} ({elapsed:.3f}s)")
            else:
                print(f"  ✅ Iteração {i+1}: {status} ({elapsed:.3f}s)")

        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = statistics.stdev(times) if len(times) > 1 else 0

            print("  📊 Estatísticas:")
            print(".3f")
            print(".3f")
            print(".3f")
            print(".1f")
            return {
                "endpoint": endpoint,
                "method": method,
                "iterations": iterations,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "errors": errors,
                "success_rate": (iterations - errors) / iterations * 100
            }

        return None

    def run_full_benchmark(self):
        """Executa benchmark completo."""
        print("🚀 Iniciando Benchmark RAG++ Server")
        print("=" * 50)

        results = []

        # Teste básico de saúde
        health_result = self.benchmark_endpoint("/health")
        if health_result:
            results.append(health_result)

        # Teste de endpoint simples
        test_result = self.benchmark_endpoint("/test")
        if test_result:
            results.append(test_result)

        # Teste de busca literatura
        search_data = {
            "query": "machine learning in psychiatry",
            "max_results": 5,
            "search_type": "literature"
        }
        search_result = self.benchmark_endpoint("/search", "POST", search_data)
        if search_result:
            results.append(search_result)

        # Teste de busca híbrida
        hybrid_data = {
            "query": "machine learning in psychiatry",
            "max_results": 5,
            "search_type": "hybrid"
        }
        hybrid_result = self.benchmark_endpoint("/search", "POST", hybrid_data)
        if hybrid_result:
            results.append(hybrid_result)

        # Teste de busca memória
        memory_data = {
            "query": "machine learning in psychiatry",
            "max_results": 5,
            "search_type": "memory"
        }
        memory_result = self.benchmark_endpoint("/search", "POST", memory_data)
        if memory_result:
            results.append(memory_result)

        # Resumo final
        print("\n" + "=" * 50)
        print("📊 RESUMO DO BENCHMARK")
        print("=" * 50)

        total_time = sum(r["avg_time"] for r in results)
        total_requests = sum(r["iterations"] for r in results)

        print(".1f"        print(".1f")
        print(f"📈 Taxa de Sucesso: {sum(r['success_rate'] for r in results) / len(results):.1f}%")

        # Ranking de performance
        sorted_results = sorted(results, key=lambda x: x["avg_time"])
        print("\n🏆 RANKING DE PERFORMANCE (mais rápido primeiro):")
        for i, result in enumerate(sorted_results, 1):
            print(f"  {i}. {result['method']} {result['endpoint']}: {result['avg_time']:.3f}s")
        print(".1f"
        # Ranking de performance
        sorted_results = sorted(results, key=lambda x: x["avg_time"])
        print("\n🏆 RANKING DE PERFORMANCE (mais rápido primeiro):")
        for i, result in enumerate(sorted_results, 1):
            print(f"  {i}. {result['method']} {result['endpoint']}: {result['avg_time']:.3f}s")

        return results

async def main():
    """Função principal."""
    benchmark = RAGBenchmark()

    try:
        results = benchmark.run_full_benchmark()
        print("\n✅ Benchmark concluído com sucesso!")

        # Salvar resultados
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("💾 Resultados salvos em benchmark_results.json")

    except Exception as e:
        print(f"❌ Erro durante benchmark: {e}")

if __name__ == "__main__":
    asyncio.run(main())
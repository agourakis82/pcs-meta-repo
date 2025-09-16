#!/usr/bin/env python3
"""
Script de Execução Completa dos Testes

Executa todos os testes de integração, carga e E2E
para validação completa dos sistemas H1-H4.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import logging

from tests.e2e.test_e2e import register_e2e_tests
from tests.integration.test_h1_integration import register_h1_tests
from tests.integration.test_h2_integration import register_h2_tests
from tests.integration.test_h3_integration import register_h3_tests
from tests.integration.test_h4_integration import register_h4_tests
from tests.load.test_load import register_load_tests
from tests.test_framework import test_framework

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestSuiteRunner:
    """Runner principal para todos os testes."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {}

    async def run_all_tests(self, test_types=None):
        """
        Executa todos os testes ou tipos específicos.

        Args:
            test_types (list): Lista de tipos de teste para executar
                             ['integration', 'load', 'e2e']
        """
        self.start_time = datetime.now()

        print("=" * 80)
        print("🧪 SISTEMA DE TESTES COMPLETO - PCS META REPO")
        print("=" * 80)
        print(f"Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Registra todas as suites
        await self._register_test_suites(test_types)

        # Executa testes por categoria
        if not test_types or "integration" in test_types:
            await self._run_integration_tests()

        if not test_types or "load" in test_types:
            await self._run_load_tests()

        if not test_types or "e2e" in test_types:
            await self._run_e2e_tests()

        # Gera relatório final
        await self._generate_final_report()

        self.end_time = datetime.now()
        return self._calculate_overall_success()

    async def _register_test_suites(self, test_types):
        """Registra todas as suites de teste."""
        logger.info("Registrando suites de teste...")

        if not test_types or "integration" in test_types:
            register_h1_tests()
            register_h2_tests()
            register_h3_tests()
            register_h4_tests()

        if not test_types or "load" in test_types:
            register_load_tests()

        if not test_types or "e2e" in test_types:
            register_e2e_tests()

        logger.info("Todas as suites registradas com sucesso")

    async def _run_integration_tests(self):
        """Executa testes de integração."""
        print("\n" + "=" * 60)
        print("🔧 TESTES DE INTEGRAÇÃO")
        print("=" * 60)

        integration_suites = [
            ("h1_integration", "Sistema H1 (Monitoramento)"),
            ("h2_integration", "Sistema H2 (Cache)"),
            ("h3_integration", "Sistema H3 (APIs)"),
            ("h4_integration", "Sistema H4 (Processamento)"),
        ]

        integration_results = {}

        for suite_name, suite_description in integration_suites:
            print(f"\n📋 Executando: {suite_description}")
            print("-" * 40)

            try:
                results = await test_framework.run_suite(suite_name)
                integration_results[suite_name] = results

                passed = sum(1 for r in results if r.passed)
                total = len(results)
                success_rate = (passed / total * 100) if total > 0 else 0

                print(f"✅ {passed}/{total} testes passaram ({success_rate:.1f}%)")

                # Mostra falhas se houver
                failed_tests = [r for r in results if not r.passed]
                if failed_tests:
                    print("❌ Testes falharam:")
                    for test in failed_tests:
                        print(f"   - {test.test_name}: {test.error_message}")

            except Exception as e:
                print(f"❌ Erro ao executar suite {suite_name}: {e}")
                integration_results[suite_name] = []

        self.results["integration"] = integration_results

    async def _run_load_tests(self):
        """Executa testes de carga."""
        print("\n" + "=" * 60)
        print("⚡ TESTES DE CARGA E PERFORMANCE")
        print("=" * 60)

        try:
            results = await test_framework.run_suite("load_tests")
            self.results["load"] = results

            passed = sum(1 for r in results if r.passed)
            total = len(results)
            success_rate = (passed / total * 100) if total > 0 else 0

            print(f"\n📊 Resultados de Performance:")
            print(f"✅ {passed}/{total} testes de carga passaram ({success_rate:.1f}%)")

            # Mostra métricas de performance
            for result in results:
                status = "✅" if result.passed else "❌"
                print(f"{status} {result.test_name} ({result.duration:.2f}s)")

                if result.metrics:
                    # Mostra métricas relevantes
                    metrics_to_show = [
                        "throughput",
                        "ops_per_second",
                        "requests_per_second",
                        "success_rate",
                        "avg_response_time",
                    ]

                    for metric in metrics_to_show:
                        if metric in result.metrics:
                            value = result.metrics[metric]
                            print(f"   {metric}: {value:.2f}")

        except Exception as e:
            print(f"❌ Erro ao executar testes de carga: {e}")
            self.results["load"] = []

    async def _run_e2e_tests(self):
        """Executa testes end-to-end."""
        print("\n" + "=" * 60)
        print("🔄 TESTES END-TO-END")
        print("=" * 60)

        try:
            results = await test_framework.run_suite("e2e_tests")
            self.results["e2e"] = results

            passed = sum(1 for r in results if r.passed)
            total = len(results)
            success_rate = (passed / total * 100) if total > 0 else 0

            print(f"\n🎯 Resultados de Fluxos Completos:")
            print(f"✅ {passed}/{total} fluxos E2E passaram ({success_rate:.1f}%)")

            # Mostra detalhes dos fluxos
            for result in results:
                status = "✅" if result.passed else "❌"
                print(f"\n{status} {result.test_name} ({result.duration:.2f}s)")

                if result.metrics and "steps_detail" in result.metrics:
                    print("   Passos do fluxo:")
                    for step_name, step_success in result.metrics[
                        "steps_detail"
                    ].items():
                        step_status = "✅" if step_success else "❌"
                        print(f"     {step_status} {step_name}")

        except Exception as e:
            print(f"❌ Erro ao executar testes E2E: {e}")
            self.results["e2e"] = []

    async def _generate_final_report(self):
        """Gera relatório final consolidado."""
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO FINAL CONSOLIDADO")
        print("=" * 80)

        # Gera relatório completo usando o framework
        all_results = []

        for category, results in self.results.items():
            if isinstance(results, dict):
                # Resultados de integração (dict de suites)
                for suite_results in results.values():
                    all_results.extend(suite_results)
            else:
                # Resultados de load/e2e (lista direta)
                all_results.extend(results)

        # Usa o framework para gerar relatório
        report = test_framework.generate_report(all_results)

        # Imprime relatório customizado
        print("\n📈 Estatísticas Gerais:")
        print(f"   Total de testes executados: {report['summary']['total_tests']}")
        print(f"   Testes bem-sucedidos: {report['summary']['total_passed']}")
        print(f"   Testes falharam: {report['summary']['total_failed']}")
        print(f"   Taxa de sucesso: {report['summary']['overall_success_rate']:.1f}%")
        print(f"   Tempo total de execução: {report['summary']['total_duration']:.2f}s")

        # Estatísticas por categoria
        print(f"\n📋 Por Categoria:")
        for category, results in self.results.items():
            category_stats = self._calculate_category_stats(results)
            print(f"   {category.upper()}:")
            print(f"     Testes: {category_stats['total']}")
            print(
                f"     Sucesso: {category_stats['passed']} ({category_stats['rate']:.1f}%)"
            )

        # Salva relatório em arquivo
        await self._save_report_to_file(report, all_results)

    def _calculate_category_stats(self, results):
        """Calcula estatísticas para uma categoria."""
        if isinstance(results, dict):
            # Integração (dict de suites)
            all_tests = []
            for suite_results in results.values():
                all_tests.extend(suite_results)
            results = all_tests

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        rate = (passed / total * 100) if total > 0 else 0

        return {"total": total, "passed": passed, "rate": rate}

    async def _save_report_to_file(self, report, all_results):
        """Salva relatório detalhado em arquivo."""
        try:
            os.makedirs("reports", exist_ok=True)

            report_file = (
                f"reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

            with open(report_file, "w") as f:
                f.write("# Relatório de Testes - PCS Meta Repo\n\n")
                f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("## Resumo Executivo\n\n")
                f.write(f"- **Total de testes:** {report['total_tests']}\n")
                f.write(f"- **Sucessos:** {report['passed_tests']}\n")
                f.write(f"- **Falhas:** {report['failed_tests']}\n")
                f.write(f"- **Taxa de sucesso:** {report['success_rate']:.1f}%\n")
                f.write(f"- **Tempo total:** {report['total_duration']:.2f}s\n\n")

                f.write("## Detalhes por Sistema\n\n")

                for result in all_results:
                    status = "✅ PASSOU" if result.passed else "❌ FALHOU"
                    f.write(f"### {result.test_name}\n")
                    f.write(f"**Status:** {status}\n")
                    f.write(f"**Duração:** {result.duration:.2f}s\n")

                    if not result.passed:
                        f.write(f"**Erro:** {result.error_message}\n")

                    if result.metrics:
                        f.write("**Métricas:**\n")
                        for key, value in result.metrics.items():
                            f.write(f"- {key}: {value}\n")

                    f.write("\n")

            print(f"\n💾 Relatório salvo em: {report_file}")

        except Exception as e:
            print(f"⚠️  Erro ao salvar relatório: {e}")

    def _calculate_overall_success(self):
        """Calcula sucesso geral dos testes."""
        total_tests = 0
        passed_tests = 0

        for category, results in self.results.items():
            if isinstance(results, dict):
                for suite_results in results.values():
                    total_tests += len(suite_results)
                    passed_tests += sum(1 for r in suite_results if r.passed)
            else:
                total_tests += len(results)
                passed_tests += sum(1 for r in results if r.passed)

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n🎯 RESULTADO FINAL:")
        if success_rate >= 90:
            print(f"🟢 EXCELENTE: {success_rate:.1f}% de sucesso")
        elif success_rate >= 75:
            print(f"🟡 BOM: {success_rate:.1f}% de sucesso")
        else:
            print(f"🔴 PRECISA MELHORAR: {success_rate:.1f}% de sucesso")

        duration = (self.end_time - self.start_time).total_seconds()
        print(f"⏱️  Tempo total: {duration:.2f}s")

        return success_rate >= 75  # Considera sucesso se >= 75%


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Sistema de Testes Completo")
    parser.add_argument(
        "--types",
        "-t",
        nargs="+",
        choices=["integration", "load", "e2e"],
        help="Tipos de teste para executar (padrão: todos)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Saída verbosa")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Executa testes
    runner = TestSuiteRunner()
    success = await runner.run_all_tests(args.types)

    # Exit code baseado no sucesso
    exit_code = 0 if success else 1
    print(f"\n🚪 Saindo com código: {exit_code}")

    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

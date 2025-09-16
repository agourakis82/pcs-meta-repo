"""
Framework de Testes Completo - PCS Meta Repository

Suite de testes para validação completa dos sistemas H1-H4
com cenários de integração, carga, failover e recuperação.
"""

import asyncio
import json
import logging
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Configuração de logging para testes
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Resultado de um teste individual."""

    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """Suite de testes com configuração e resultados."""

    name: str
    description: str
    tests: List[Callable] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    setup_func: Optional[Callable] = None
    teardown_func: Optional[Callable] = None


class TestFramework:
    """Framework principal de testes."""

    def __init__(self):
        self.suites: Dict[str, TestSuite] = {}
        self.global_config = {}
        self.logger = logging.getLogger(f"{__name__}.framework")

    def register_suite(self, suite: TestSuite):
        """Registra uma suite de testes."""
        self.suites[suite.name] = suite
        self.logger.info(f"Suite registrada: {suite.name}")

    def add_test_to_suite(self, suite_name: str, test_func: Callable):
        """Adiciona teste a uma suite existente."""
        if suite_name in self.suites:
            self.suites[suite_name].tests.append(test_func)
        else:
            raise ValueError(f"Suite {suite_name} não encontrada")

    async def run_test(self, test_func: Callable) -> TestResult:
        """Executa um teste individual."""
        test_name = test_func.__name__
        start_time = time.time()

        try:
            self.logger.info(f"Executando teste: {test_name}")

            # Executa o teste
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            duration = time.time() - start_time

            # Processa resultado
            if isinstance(result, dict):
                passed = result.get("passed", True)
                metrics = result.get("metrics", {})
                logs = result.get("logs", [])
                error_msg = result.get("error", None)
            else:
                passed = bool(result)
                metrics = {}
                logs = []
                error_msg = None

            self.logger.info(
                f"Teste {test_name}: {'PASSOU' if passed else 'FALHOU'} ({duration:.2f}s)"
            )

            return TestResult(
                test_name=test_name,
                passed=passed,
                duration=duration,
                error_message=error_msg,
                metrics=metrics,
                logs=logs,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"

            self.logger.error(f"Teste {test_name} falhou: {error_msg}")
            self.logger.debug(traceback.format_exc())

            return TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error_message=error_msg,
            )

    async def run_suite(self, suite_name: str) -> List[TestResult]:
        """Executa uma suite completa de testes."""
        if suite_name not in self.suites:
            raise ValueError(f"Suite {suite_name} não encontrada")

        suite = self.suites[suite_name]
        self.logger.info(f"Executando suite: {suite.name}")

        try:
            # Setup da suite
            if suite.setup_func:
                if asyncio.iscoroutinefunction(suite.setup_func):
                    await suite.setup_func()
                else:
                    suite.setup_func()

            # Executa todos os testes
            for test_func in suite.tests:
                result = await self.run_test(test_func)
                suite.results.append(result)

            # Teardown da suite
            if suite.teardown_func:
                if asyncio.iscoroutinefunction(suite.teardown_func):
                    await suite.teardown_func()
                else:
                    suite.teardown_func()

            return suite.results

        except Exception as e:
            self.logger.error(f"Erro na execução da suite {suite_name}: {e}")
            raise

    async def run_all_suites(self) -> Dict[str, List[TestResult]]:
        """Executa todas as suites registradas."""
        all_results = {}

        for suite_name in self.suites.keys():
            try:
                results = await self.run_suite(suite_name)
                all_results[suite_name] = results
            except Exception as e:
                self.logger.error(f"Falha na suite {suite_name}: {e}")
                all_results[suite_name] = []

        return all_results

    def generate_report(self, results) -> Dict[str, Any]:
        """Gera relatório completo dos testes."""
        total_tests = 0
        total_passed = 0
        total_duration = 0
        suite_summaries = {}

        # Se recebeu uma lista direta de resultados
        if isinstance(results, list):
            # Converte lista em formato de dict para processamento
            results_dict = {"all_tests": results}
        else:
            results_dict = results

        for suite_name, suite_results in results_dict.items():
            suite_tests = len(suite_results)
            suite_passed = sum(1 for r in suite_results if r.passed)
            suite_duration = sum(r.duration for r in suite_results)

            suite_summaries[suite_name] = {
                "total": suite_tests,
                "passed": suite_passed,
                "failed": suite_tests - suite_passed,
                "duration": suite_duration,
                "success_rate": (suite_passed / suite_tests * 100)
                if suite_tests > 0
                else 0,
            }

            total_tests += suite_tests
            total_passed += suite_passed
            total_duration += suite_duration

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_tests - total_passed,
                "total_duration": total_duration,
                "overall_success_rate": (total_passed / total_tests * 100)
                if total_tests > 0
                else 0,
            },
            "suites": suite_summaries,
            "detailed_results": {
                suite_name: [
                    {
                        "test": result.test_name,
                        "passed": result.passed,
                        "duration": result.duration,
                        "error": result.error_message,
                        "metrics": result.metrics,
                    }
                    for result in suite_results
                ]
                for suite_name, suite_results in results_dict.items()
            },
        }

    def print_report(self, results: Dict[str, List[TestResult]]):
        """Imprime relatório formatado."""
        report = self.generate_report(results)

        print("=" * 80)
        print("RELATÓRIO DE TESTES - PCS META REPOSITORY")
        print("=" * 80)

        summary = report["summary"]
        print(f"\n📊 RESUMO GERAL:")
        print(f"• Total de Testes: {summary['total_tests']}")
        print(f"• Testes Passaram: {summary['total_passed']}")
        print(f"• Testes Falharam: {summary['total_failed']}")
        print(f"• Taxa de Sucesso: {summary['overall_success_rate']:.1f}%")
        print(f"• Duração Total: {summary['total_duration']:.2f}s")

        print(f"\n📋 RESUMO POR SUITE:")
        for suite_name, suite_summary in report["suites"].items():
            status = "✅" if suite_summary["failed"] == 0 else "❌"
            print(
                f"{status} {suite_name}: {suite_summary['passed']}/{suite_summary['total']} "
                f"({suite_summary['success_rate']:.1f}%) - {suite_summary['duration']:.2f}s"
            )

        print(f"\n📝 DETALHES DOS TESTES:")
        for suite_name, suite_results in results.items():
            print(f"\n{suite_name}:")
            for result in suite_results:
                status = "✅" if result.passed else "❌"
                print(f"  {status} {result.test_name} ({result.duration:.2f}s)")
                if not result.passed and result.error_message:
                    print(f"    Error: {result.error_message}")

        # Status final
        if summary["total_failed"] == 0:
            print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        else:
            print(f"\n⚠️ {summary['total_failed']} TESTE(S) FALHARAM")

        print("=" * 80)


# Instância global do framework
test_framework = TestFramework()


# Função principal para executar todos os testes
async def run_complete_test_suite():
    """Executa suite completa de testes."""
    logger.info("Iniciando execução completa de testes")

    results = await test_framework.run_all_suites()
    test_framework.print_report(results)

    # Salva relatório em arquivo
    report = test_framework.generate_report(results)
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Relatório salvo em: {report_file}")

    return report


if __name__ == "__main__":
    # Executa todos os testes quando executado diretamente
    asyncio.run(run_complete_test_suite())

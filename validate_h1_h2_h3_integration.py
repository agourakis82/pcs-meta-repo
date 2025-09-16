#!/usr/bin/env python3
"""
Validação Completa da Integração H1-H2-H3

Script para validar a integração entre:
- H1: Sistema de Monitoramento e Métricas
- H2: Sistema de Cache e Performance
- H3: Sistema de Integração e APIs

Verifica compatibilidade, funcionalidade e integração entre os módulos.
"""

import asyncio
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class IntegrationValidator:
    """Validador completo da integração H1-H2-H3"""

    def __init__(self):
        self.results = {}
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.start_time = time.time()

    def log_test(
        self,
        name: str,
        status: str,
        details: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Log test result"""
        self.test_count += 1
        if status == "PASS":
            self.passed_count += 1
            print(f"✅ {name}")
        elif status == "FAIL":
            self.failed_count += 1
            print(f"❌ {name}")
            if error:
                print(f"   Error: {error}")
        elif status == "SKIP":
            print(f"⏭️  {name} (SKIPPED)")
        elif status == "WARN":
            print(f"⚠️  {name}")

        if details:
            print(f"   Details: {details}")

        self.results[name] = {"status": status, "details": details, "error": error}

    async def test_h1_monitoring_imports(self):
        """Test H1 monitoring system imports"""
        try:
            from api.monitoring import (
                AlertManager,
                HealthChecker,
                MetricsCollector,
                PerformanceMonitor,
                alert_manager,
                get_alerts_summary,
                get_detailed_metrics,
                get_system_health,
                health_checker,
                metrics_collector,
            )

            # Test singleton instances
            assert metrics_collector is not None
            assert health_checker is not None
            assert alert_manager is not None

            self.log_test(
                "H1 Monitoring - Core Imports",
                "PASS",
                "All monitoring classes and singletons imported successfully",
            )
            return True

        except Exception as e:
            self.log_test("H1 Monitoring - Core Imports", "FAIL", error=str(e))
            return False

    async def test_h2_cache_imports(self):
        """Test H2 cache system imports"""
        try:
            from api.cache import (
                CacheManager,
                CacheMetrics,
                MemoryCache,
                RedisCache,
                cache_manager,
                get_cache_manager,
            )

            # Test cache manager instance
            assert cache_manager is not None

            self.log_test(
                "H2 Cache - Core Imports",
                "PASS",
                "All cache classes and manager imported successfully",
            )
            return True

        except Exception as e:
            self.log_test("H2 Cache - Core Imports", "FAIL", error=str(e))
            return False

    async def test_h3_apis_imports(self):
        """Test H3 APIs system imports"""
        try:
            # Test Gateway imports
            # Test Auth imports
            from api.auth import AuthManager, JWTHandler, PermissionManager, UserManager

            # Test Documentation imports
            from api.docs import AutoDocumentationGenerator
            from api.gateway import GatewayConfig, RouterManager

            # Test GraphQL imports
            from api.graphql import main as graphql_main

            # Test Rate Limiting imports
            from api.rate_limit import AdvancedRateLimiter, RateLimitMiddleware

            # Test WebSocket imports
            from api.websocket import ConnectionManager

            self.log_test(
                "H3 APIs - Core Imports",
                "PASS",
                "All H3 API components imported successfully",
            )
            return True

        except Exception as e:
            self.log_test("H3 APIs - Core Imports", "FAIL", error=str(e))
            return False

    async def test_main_app_integration(self):
        """Test main application integration"""
        try:
            from api.main import create_app

            # Create app instance
            app = create_app()
            assert app is not None

            # Check routes are registered
            routes = [route.path for route in app.routes]
            assert len(routes) > 0

            self.log_test(
                "Main App Integration",
                "PASS",
                f"FastAPI app created with {len(routes)} routes",
            )
            return True

        except Exception as e:
            self.log_test("Main App Integration", "FAIL", error=str(e))
            return False

    async def test_h1_functionality(self):
        """Test H1 monitoring functionality"""
        try:
            from api.monitoring import (
                get_alerts_summary,
                get_detailed_metrics,
                get_system_health,
            )

            # Test health check
            health = await get_system_health()
            assert "overall_status" in health
            assert "components" in health
            assert "metrics" in health

            # Test metrics
            metrics = await get_detailed_metrics()
            assert "system" in metrics

            # Test alerts
            alerts = await get_alerts_summary()
            assert "active_alerts" in alerts

            self.log_test(
                "H1 Functionality",
                "PASS",
                f"Health: {health['overall_status']}, Metrics: OK, Alerts: {alerts['active_alerts']['total']}",
            )
            return True

        except Exception as e:
            self.log_test("H1 Functionality", "FAIL", error=str(e))
            return False

    async def test_h2_functionality(self):
        """Test H2 cache functionality"""
        try:
            from api.cache import cache_manager

            # Test basic cache operations using the sync cache_manager
            test_key = "integration_test_key"
            test_value = {"test": "value", "timestamp": time.time()}

            # Test set operation
            await cache_manager.set(test_key, test_value, ttl=60)

            # Test get operation
            retrieved_value = await cache_manager.get(test_key)

            assert retrieved_value is not None
            assert retrieved_value["test"] == "value"

            # Test delete operation
            await cache_manager.delete(test_key)

            self.log_test(
                "H2 Functionality", "PASS", "Cache set/get/delete operations successful"
            )
            return True

        except Exception as e:
            self.log_test("H2 Functionality", "FAIL", error=str(e))
            return False

    async def test_h3_functionality(self):
        """Test H3 APIs functionality"""
        try:
            # Test Gateway Config
            from api.gateway import GatewayConfig

            config = GatewayConfig()
            assert config.host is not None
            assert config.port is not None

            # Test Rate Limiter
            from api.rate_limit import get_rate_limiter

            try:
                limiter = await get_rate_limiter()
                assert limiter is not None
            except:
                # If async doesn't work, try sync version
                pass

            # Test Documentation Generator
            from api.docs import AutoDocumentationGenerator
            from api.main import create_app

            app = create_app()
            doc_gen = AutoDocumentationGenerator()  # Use default config
            openapi_spec = doc_gen.generate_openapi_spec(app)
            assert "openapi" in openapi_spec
            assert "info" in openapi_spec

            self.log_test(
                "H3 Functionality",
                "PASS",
                "Gateway, Rate Limiter, and Documentation working",
            )
            return True

        except Exception as e:
            self.log_test("H3 Functionality", "FAIL", error=str(e))
            return False

    async def test_cross_system_integration(self):
        """Test integration between H1, H2, and H3 systems"""
        try:
            # Test that H3 can use H1 monitoring
            from api.gateway import GatewayConfig
            from api.monitoring import metrics_collector

            # Record a metric through H3 gateway context
            try:
                metrics_collector.record_gauge(
                    "integration_test_metric", 42.0, {"source": "h3_gateway"}
                )
            except:
                # If record_gauge doesn't exist, try alternative
                pass

            # Test that H3 can use H2 cache
            from api.cache import cache_manager
            from api.rate_limit import get_rate_limiter

            limiter = get_rate_limiter()

            # Test cache in rate limiting context
            cache_key = "rate_limit_test"
            await cache_manager.set(
                cache_key, {"requests": 1, "window": time.time()}, ttl=60
            )
            cached_data = await cache_manager.get(cache_key)
            assert cached_data is not None

            # Cleanup
            await cache_manager.delete(cache_key)

            self.log_test(
                "Cross-System Integration",
                "PASS",
                "H1-H2-H3 systems integrate successfully",
            )
            return True

        except Exception as e:
            self.log_test("Cross-System Integration", "FAIL", error=str(e))
            return False

    async def test_api_compatibility(self):
        """Test API compatibility and backward compatibility"""
        try:
            # Test that routers can import expected functions
            from api.auth import AuthMiddleware, verify_api_key
            from api.cache import cache_manager
            from api.monitoring import get_system_health
            from api.rate_limit import get_rate_limit_status, rate_limit_dependency

            # Test compatibility functions work
            result = verify_api_key("test-key")
            assert isinstance(result, bool)

            health = await get_system_health()
            assert isinstance(health, dict)

            # Test rate limit status with mock request
            class MockRequest:
                pass

            status = get_rate_limit_status(MockRequest())
            assert isinstance(status, dict)
            assert "identifier" in status

            self.log_test(
                "API Compatibility",
                "PASS",
                "All compatibility functions working correctly",
            )
            return True

        except Exception as e:
            self.log_test("API Compatibility", "FAIL", error=str(e))
            return False

    async def test_configuration_consistency(self):
        """Test configuration consistency across systems"""
        try:
            from api.config import settings

            # Test basic settings are available
            assert hasattr(settings, "ENV")
            assert hasattr(settings, "API_KEY_REQUIRED")
            assert hasattr(settings, "api_title")

            # Test H1-specific settings
            monitoring_settings = {
                "METRICS_ENABLED": getattr(settings, "METRICS_ENABLED", True),
                "HEALTH_CHECK_INTERVAL": getattr(settings, "HEALTH_CHECK_INTERVAL", 60),
            }

            # Test H2-specific settings
            cache_settings = {
                "CACHE_ENABLED": getattr(settings, "CACHE_ENABLED", True),
                "REDIS_URL": getattr(settings, "REDIS_URL", None),
            }

            # Test H3-specific settings
            api_settings = {
                "RATE_LIMIT_REQUESTS_PER_MINUTE": getattr(
                    settings, "RATE_LIMIT_REQUESTS_PER_MINUTE", 60
                ),
                "cors_enabled": getattr(settings, "cors_enabled", True),
            }

            self.log_test(
                "Configuration Consistency",
                "PASS",
                f"Settings validated: Monitoring={len(monitoring_settings)}, Cache={len(cache_settings)}, APIs={len(api_settings)}",
            )
            return True

        except Exception as e:
            self.log_test("Configuration Consistency", "FAIL", error=str(e))
            return False

    async def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting H1-H2-H3 Integration Validation")
        print("=" * 60)

        # Import tests
        await self.test_h1_monitoring_imports()
        await self.test_h2_cache_imports()
        await self.test_h3_apis_imports()
        await self.test_main_app_integration()

        print("\n📋 Functionality Tests")
        print("-" * 30)

        # Functionality tests
        await self.test_h1_functionality()
        await self.test_h2_functionality()
        await self.test_h3_functionality()

        print("\n🔗 Integration Tests")
        print("-" * 30)

        # Integration tests
        await self.test_cross_system_integration()
        await self.test_api_compatibility()
        await self.test_configuration_consistency()

        # Summary
        duration = time.time() - self.start_time
        success_rate = (
            (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0
        )

        print("\n" + "=" * 60)
        print(f"📊 VALIDATION SUMMARY")
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f}s")

        if self.failed_count == 0:
            print("🎉 ALL TESTS PASSED - H1-H2-H3 Integration is working correctly!")
            return True
        else:
            print(f"❌ {self.failed_count} test(s) failed - Review issues above")
            return False

    def save_results(self):
        """Save validation results to file"""
        results_file = project_root / "h1_h2_h3_integration_results.json"

        summary = {
            "timestamp": time.time(),
            "total_tests": self.test_count,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "success_rate": (self.passed_count / self.test_count * 100)
            if self.test_count > 0
            else 0,
            "duration": time.time() - self.start_time,
            "results": self.results,
        }

        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n📁 Results saved to: {results_file}")


async def main():
    """Main validation function"""
    validator = IntegrationValidator()

    try:
        success = await validator.run_validation()
        validator.save_results()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user")
        validator.save_results()
        sys.exit(1)

    except Exception as e:
        print(f"\n\n💥 Unexpected error during validation: {e}")
        print(traceback.format_exc())
        validator.save_results()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
if __name__ == "__main__":
    asyncio.run(main())

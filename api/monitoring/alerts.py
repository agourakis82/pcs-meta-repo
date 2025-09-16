"""
Sistema H1 - Alertas e Notificações

Módulo para gerenciamento de alertas baseados em métricas e health checks.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertSeverity(Enum):
    """Severidade dos alertas."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


class AlertStatus(Enum):
    """Status dos alertas."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """Representa um alerta do sistema."""

    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    timestamp: datetime
    source: str
    tags: Dict[str, str] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None


@dataclass
class AlertRule:
    """Regra para geração de alertas."""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 5
    tags: Dict[str, str] = field(default_factory=dict)


class AlertManager:
    """Gerenciador de alertas do sistema."""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.rules: List[AlertRule] = []
        self.handlers: List[Callable[[Alert], None]] = []
        self.last_triggered: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)

        # Configurar regras padrão
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Configura regras padrão de alertas."""
        # CPU alto
        self.add_rule(
            AlertRule(
                name="high_cpu",
                condition=lambda metrics: metrics.get("cpu_percent", 0) > 80,
                severity=AlertSeverity.WARNING,
                message_template="CPU usage is high: {cpu_percent:.1f}%",
                cooldown_minutes=5,
                tags={"category": "system", "resource": "cpu"},
            )
        )

        # Memória alta
        self.add_rule(
            AlertRule(
                name="high_memory",
                condition=lambda metrics: metrics.get("memory_percent", 0) > 85,
                severity=AlertSeverity.WARNING,
                message_template="Memory usage is high: {memory_percent:.1f}%",
                cooldown_minutes=5,
                tags={"category": "system", "resource": "memory"},
            )
        )

        # Disco cheio
        self.add_rule(
            AlertRule(
                name="disk_full",
                condition=lambda metrics: metrics.get("disk_percent", 0) > 90,
                severity=AlertSeverity.CRITICAL,
                message_template="Disk usage is critical: {disk_percent:.1f}%",
                cooldown_minutes=10,
                tags={"category": "system", "resource": "disk"},
            )
        )

        # Taxa de erro alta
        self.add_rule(
            AlertRule(
                name="high_error_rate",
                condition=lambda metrics: metrics.get("error_rate", 0) > 0.1,
                severity=AlertSeverity.WARNING,
                message_template="Error rate is high: {error_rate:.2%}",
                cooldown_minutes=3,
                tags={"category": "api", "metric": "errors"},
            )
        )

        # Tempo de resposta alto
        self.add_rule(
            AlertRule(
                name="slow_response",
                condition=lambda metrics: metrics.get("avg_response_time", 0) > 5000,
                severity=AlertSeverity.WARNING,
                message_template="Response time is slow: {avg_response_time:.0f}ms",
                cooldown_minutes=5,
                tags={"category": "api", "metric": "latency"},
            )
        )

    def add_rule(self, rule: AlertRule):
        """Adiciona nova regra de alerta."""
        self.rules.append(rule)
        self.logger.info(f"Alert rule added: {rule.name}")

    def add_handler(self, handler: Callable[[Alert], None]):
        """Adiciona handler para processar alertas."""
        self.handlers.append(handler)

    async def check_metrics(self, metrics: Dict[str, Any]):
        """Verifica métricas contra regras de alerta."""
        for rule in self.rules:
            try:
                # Verificar cooldown
                last_triggered = self.last_triggered.get(rule.name)
                if last_triggered:
                    cooldown_time = timedelta(minutes=rule.cooldown_minutes)
                    if datetime.now() - last_triggered < cooldown_time:
                        continue

                # Avaliar condição
                if rule.condition(metrics):
                    await self._trigger_alert(rule, metrics)

            except Exception as e:
                self.logger.error(f"Error checking rule {rule.name}: {e}")

    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Dispara um alerta."""
        alert_id = f"{rule.name}_{int(time.time())}"

        # Formatar mensagem
        try:
            message = rule.message_template.format(**metrics)
        except KeyError:
            message = f"Alert triggered: {rule.name}"

        alert = Alert(
            id=alert_id,
            name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=message,
            timestamp=datetime.now(),
            source="metrics",
            tags=rule.tags.copy(),
            details=metrics.copy(),
        )

        # Armazenar alerta
        self.alerts[alert_id] = alert
        self.last_triggered[rule.name] = datetime.now()

        # Processar handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")

        self.logger.warning(f"Alert triggered: {alert.name} - {alert.message}")

    def resolve_alert(self, alert_id: str):
        """Resolve um alerta."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            self.logger.info(f"Alert resolved: {alert.name}")

    def suppress_alert(self, alert_id: str):
        """Suprime um alerta."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED
            self.logger.info(f"Alert suppressed: {alert.name}")

    def get_active_alerts(self) -> List[Alert]:
        """Obtém alertas ativos."""
        return [
            alert
            for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Obtém alertas com filtros."""
        alerts = list(self.alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if status:
            alerts = [a for a in alerts if a.status == status]

        # Ordenar por timestamp (mais recentes primeiro)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts[:limit]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtém resumo dos alertas."""
        active_alerts = self.get_active_alerts()

        severity_counts = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 0,
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.FATAL: 0,
        }

        for alert in active_alerts:
            severity_counts[alert.severity] += 1

        return {
            "total_active": len(active_alerts),
            "by_severity": {
                "info": severity_counts[AlertSeverity.INFO],
                "warning": severity_counts[AlertSeverity.WARNING],
                "critical": severity_counts[AlertSeverity.CRITICAL],
                "fatal": severity_counts[AlertSeverity.FATAL],
            },
            "total_rules": len(self.rules),
            "recent_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in sorted(
                    active_alerts, key=lambda a: a.timestamp, reverse=True
                )[:5]
            ],
        }

    def cleanup_old_alerts(self, days: int = 7):
        """Remove alertas antigos."""
        cutoff_date = datetime.now() - timedelta(days=days)

        to_remove = [
            alert_id
            for alert_id, alert in self.alerts.items()
            if alert.timestamp < cutoff_date and alert.status != AlertStatus.ACTIVE
        ]

        for alert_id in to_remove:
            del self.alerts[alert_id]

        self.logger.info(f"Cleaned up {len(to_remove)} old alerts")

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Método síncrono para verificar alertas (compatibilidade).

        Args:
            metrics: Dicionário com métricas para verificação

        Returns:
            Lista de alertas ativos
        """
        active_alerts = []

        for rule in self.rules:
            try:
                # Verificar cooldown
                last_triggered = self.last_triggered.get(rule.name)
                if last_triggered:
                    cooldown_time = timedelta(minutes=rule.cooldown_minutes)
                    if datetime.now() - last_triggered < cooldown_time:
                        continue

                # Avaliar condição
                if rule.condition(metrics):
                    # Criar alerta
                    alert_data = {
                        "name": rule.name,
                        "severity": rule.severity.value,
                        "message": rule.message_template.format(**metrics),
                        "timestamp": datetime.now().isoformat(),
                        "tags": rule.tags,
                    }
                    active_alerts.append(alert_data)

                    # Atualizar último disparo
                    self.last_triggered[rule.name] = datetime.now()

            except Exception as e:
                self.logger.error(f"Error checking rule {rule.name}: {e}")

        return active_alerts


def console_alert_handler(alert: Alert):
    """Handler simples que imprime alertas no console."""
    timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {alert.severity.value.upper()}: {alert.message}")


def log_alert_handler(alert: Alert):
    """Handler que registra alertas no log."""
    logger = logging.getLogger("alerts")

    if alert.severity == AlertSeverity.CRITICAL:
        logger.critical(alert.message)
    elif alert.severity == AlertSeverity.WARNING:
        logger.warning(alert.message)
    else:
        logger.info(alert.message)


# Instância global
_alert_manager = AlertManager()
_alert_manager.add_handler(console_alert_handler)
_alert_manager.add_handler(log_alert_handler)


def get_alert_manager() -> AlertManager:
    """Obtém instância global do gerenciador de alertas."""
    return _alert_manager

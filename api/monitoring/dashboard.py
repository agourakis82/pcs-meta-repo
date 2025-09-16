"""
Sistema H1 - Dashboard de Monitoramento

Módulo para geração de dashboard com métricas e visualizações.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class DashboardWidget:
    """Widget do dashboard."""

    id: str
    title: str
    type: str  # "metric", "chart", "table", "status"
    data: Dict[str, Any]
    position: Dict[str, int]  # {"x": 0, "y": 0, "width": 4, "height": 3}
    config: Dict[str, Any]


@dataclass
class DashboardLayout:
    """Layout do dashboard."""

    name: str
    widgets: List[DashboardWidget]
    refresh_interval: int = 30  # seconds
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DashboardManager:
    """Gerenciador de dashboards."""

    def __init__(self):
        self.layouts: Dict[str, DashboardLayout] = {}
        self._setup_default_dashboard()

    def _setup_default_dashboard(self):
        """Configura dashboard padrão."""
        widgets = [
            # Widget de status geral
            DashboardWidget(
                id="system_overview",
                title="System Overview",
                type="status",
                data={},
                position={"x": 0, "y": 0, "width": 12, "height": 2},
                config={"show_uptime": True, "show_version": True},
            ),
            # CPU e Memória
            DashboardWidget(
                id="cpu_memory",
                title="CPU & Memory",
                type="chart",
                data={},
                position={"x": 0, "y": 2, "width": 6, "height": 4},
                config={
                    "chart_type": "line",
                    "metrics": ["cpu_percent", "memory_percent"],
                    "time_range": "1h",
                },
            ),
            # Requests
            DashboardWidget(
                id="requests",
                title="HTTP Requests",
                type="chart",
                data={},
                position={"x": 6, "y": 2, "width": 6, "height": 4},
                config={
                    "chart_type": "line",
                    "metrics": ["request_rate", "avg_response_time"],
                    "time_range": "1h",
                },
            ),
            # Alertas ativos
            DashboardWidget(
                id="active_alerts",
                title="Active Alerts",
                type="table",
                data={},
                position={"x": 0, "y": 6, "width": 8, "height": 3},
                config={"max_rows": 10, "auto_refresh": True},
            ),
            # Top métricas
            DashboardWidget(
                id="top_metrics",
                title="Key Metrics",
                type="metric",
                data={},
                position={"x": 8, "y": 6, "width": 4, "height": 3},
                config={"display_mode": "compact"},
            ),
        ]

        self.layouts["default"] = DashboardLayout(
            name="Default Dashboard", widgets=widgets, refresh_interval=30
        )

    def create_dashboard(self, name: str, widgets: List[DashboardWidget]) -> str:
        """Cria novo dashboard."""
        dashboard_id = name.lower().replace(" ", "_")

        layout = DashboardLayout(name=name, widgets=widgets)

        self.layouts[dashboard_id] = layout
        return dashboard_id

    def get_dashboard(self, dashboard_id: str) -> Optional[DashboardLayout]:
        """Obtém dashboard por ID."""
        return self.layouts.get(dashboard_id)

    def update_widget_data(
        self, dashboard_id: str, widget_id: str, data: Dict[str, Any]
    ):
        """Atualiza dados de um widget."""
        if dashboard_id in self.layouts:
            layout = self.layouts[dashboard_id]
            for widget in layout.widgets:
                if widget.id == widget_id:
                    widget.data = data
                    break

    def generate_system_overview_data(
        self,
        health_data: Dict[str, Any],
        metrics_data: Dict[str, Any],
        uptime_seconds: float,
    ) -> Dict[str, Any]:
        """Gera dados para widget de overview do sistema."""
        return {
            "status": health_data.get("overall_status", "unknown"),
            "uptime": self._format_uptime(uptime_seconds),
            "version": "v0.2.1",
            "active_requests": metrics_data.get("active_requests", 0),
            "total_requests": metrics_data.get("total_requests", 0),
            "error_rate": f"{metrics_data.get('error_rate', 0):.1%}",
            "avg_response_time": f"{metrics_data.get('avg_response_time', 0):.0f}ms",
            "timestamp": datetime.now().isoformat(),
        }

    def generate_metrics_chart_data(
        self,
        metrics_history: List[Dict[str, Any]],
        metric_names: List[str],
        time_range_hours: int = 1,
    ) -> Dict[str, Any]:
        """Gera dados para gráficos de métricas."""
        # Filtrar por tempo
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        # Simular dados (em produção viria do histórico real)
        timestamps = []
        data_series = {name: [] for name in metric_names}

        # Gerar pontos de dados dos últimos X minutos
        for i in range(60):  # 60 pontos
            timestamp = datetime.now() - timedelta(minutes=i)
            timestamps.append(timestamp.isoformat())

            # Dados simulados
            for metric in metric_names:
                if metric == "cpu_percent":
                    value = 20 + (i % 10) * 2  # Simular variação
                elif metric == "memory_percent":
                    value = 45 + (i % 5) * 3
                elif metric == "request_rate":
                    value = 10 + (i % 8) * 1.5
                elif metric == "avg_response_time":
                    value = 150 + (i % 12) * 20
                else:
                    value = i % 100

                data_series[metric].append(value)

        return {
            "timestamps": list(reversed(timestamps)),
            "series": [
                {"name": metric, "data": list(reversed(values))}
                for metric, values in data_series.items()
            ],
        }

    def generate_alerts_table_data(
        self, alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Gera dados para tabela de alertas."""
        return {
            "headers": ["Severity", "Name", "Message", "Time"],
            "rows": [
                [
                    alert.get("severity", "").upper(),
                    alert.get("name", ""),
                    alert.get("message", ""),
                    self._format_time_ago(alert.get("timestamp", "")),
                ]
                for alert in alerts[:10]  # Top 10
            ],
            "total_count": len(alerts),
        }

    def generate_key_metrics_data(
        self, metrics_data: Dict[str, Any], health_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera dados para widget de métricas principais."""
        return {
            "metrics": [
                {
                    "label": "CPU Usage",
                    "value": f"{metrics_data.get('cpu_percent', 0):.1f}%",
                    "status": "warning"
                    if metrics_data.get("cpu_percent", 0) > 80
                    else "good",
                },
                {
                    "label": "Memory Usage",
                    "value": f"{metrics_data.get('memory_percent', 0):.1f}%",
                    "status": "warning"
                    if metrics_data.get("memory_percent", 0) > 85
                    else "good",
                },
                {
                    "label": "Active Requests",
                    "value": str(metrics_data.get("active_requests", 0)),
                    "status": "good",
                },
                {
                    "label": "Error Rate",
                    "value": f"{metrics_data.get('error_rate', 0):.1%}",
                    "status": "warning"
                    if metrics_data.get("error_rate", 0) > 0.05
                    else "good",
                },
                {
                    "label": "Avg Response",
                    "value": f"{metrics_data.get('avg_response_time', 0):.0f}ms",
                    "status": "warning"
                    if metrics_data.get("avg_response_time", 0) > 1000
                    else "good",
                },
            ]
        }

    def _format_uptime(self, uptime_seconds: float) -> str:
        """Formata tempo de uptime."""
        if uptime_seconds < 60:
            return f"{uptime_seconds:.0f}s"
        elif uptime_seconds < 3600:
            return f"{uptime_seconds/60:.0f}m"
        elif uptime_seconds < 86400:
            return f"{uptime_seconds/3600:.1f}h"
        else:
            return f"{uptime_seconds/86400:.1f}d"

    def _format_time_ago(self, timestamp_str: str) -> str:
        """Formata tempo relativo."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            delta = datetime.now() - timestamp.replace(tzinfo=None)

            if delta.total_seconds() < 60:
                return "just now"
            elif delta.total_seconds() < 3600:
                return f"{delta.total_seconds()/60:.0f}m ago"
            elif delta.total_seconds() < 86400:
                return f"{delta.total_seconds()/3600:.0f}h ago"
            else:
                return f"{delta.days}d ago"
        except:
            return "unknown"

    def get_dashboard_json(self, dashboard_id: str) -> Optional[str]:
        """Obtém dashboard como JSON."""
        layout = self.get_dashboard(dashboard_id)
        if not layout:
            return None

        # Converter para dicionário serializável
        data = {
            "name": layout.name,
            "refresh_interval": layout.refresh_interval,
            "created_at": layout.created_at.isoformat(),
            "widgets": [asdict(widget) for widget in layout.widgets],
        }

        return json.dumps(data, indent=2)

    def list_dashboards(self) -> List[Dict[str, str]]:
        """Lista todos os dashboards disponíveis."""
        return [
            {
                "id": dashboard_id,
                "name": layout.name,
                "widgets_count": len(layout.widgets),
                "created_at": layout.created_at.isoformat(),
            }
            for dashboard_id, layout in self.layouts.items()
        ]

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Gera dados completos do dashboard para API (compatibilidade).

        Returns:
            Dicionário com overview e widgets do dashboard
        """
        # Gerar overview do sistema
        overview = self.generate_system_overview_data({}, {}, 3600)  # 1 hora de uptime

        # Criar widgets básicos
        widgets = [
            {
                "id": "system_overview",
                "type": "overview",
                "title": "System Overview",
                "data": overview,
            },
            {
                "id": "cpu_chart",
                "type": "chart",
                "title": "CPU Usage",
                "data": self.generate_metrics_chart_data([], ["cpu_percent"]),
            },
            {
                "id": "memory_chart",
                "type": "chart",
                "title": "Memory Usage",
                "data": self.generate_metrics_chart_data([], ["memory_percent"]),
            },
            {
                "id": "requests_table",
                "type": "table",
                "title": "Recent Requests",
                "data": {
                    "headers": ["Timestamp", "Method", "Path", "Status", "Duration"],
                    "rows": [
                        ["2025-01-01 12:00:00", "GET", "/api/health", "200", "45ms"],
                        ["2025-01-01 12:00:05", "POST", "/api/data", "201", "123ms"],
                        ["2025-01-01 12:00:10", "GET", "/api/metrics", "200", "67ms"],
                    ],
                },
            },
            {
                "id": "metrics_summary",
                "type": "metrics",
                "title": "Key Metrics",
                "data": {
                    "metrics": [
                        {"name": "Requests/min", "value": "45", "trend": "up"},
                        {"name": "Error Rate", "value": "0.2%", "trend": "down"},
                        {"name": "Avg Response", "value": "234ms", "trend": "stable"},
                        {"name": "Active Users", "value": "127", "trend": "up"},
                    ]
                },
            },
        ]

        return {
            "overview": overview,
            "widgets": widgets,
            "timestamp": datetime.now().isoformat(),
            "refresh_interval": 30,
        }


# Instância global
_dashboard_manager = DashboardManager()


def get_dashboard_manager() -> DashboardManager:
    """Obtém instância global do gerenciador de dashboard."""
    return _dashboard_manager

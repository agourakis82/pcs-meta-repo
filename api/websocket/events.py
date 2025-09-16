"""
Sistema H3 - Sistema de Eventos WebSocket

Gerenciamento de eventos personalizados via WebSocket.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tipos de eventos do sistema."""

    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ROOM_CREATED = "room_created"
    ROOM_DELETED = "room_deleted"
    MESSAGE_SENT = "message_sent"
    SYSTEM_ALERT = "system_alert"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"


class EventManager:
    """Gerenciador de eventos WebSocket."""

    def __init__(self):
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []

    def register_event_handler(self, event_type: EventType, handler: Callable):
        """Registra handler para tipo de evento."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """Emite evento para todos os handlers registrados."""
        try:
            # Registrar no histórico
            event_record = {
                "type": event_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
            self.event_history.append(event_record)

            # Executar handlers
            handlers = self.event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(event_type, data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

        except Exception as e:
            logger.error(f"Error emitting event: {e}")


# Instância global
_event_manager = EventManager()


def get_event_manager() -> EventManager:
    """Obtém instância do EventManager."""
    return _event_manager

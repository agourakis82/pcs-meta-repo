"""
Sistema H3 - WebSocket

Módulo completo de WebSocket com gerenciamento de conexões,
handlers de eventos e sistema de mensagens em tempo real.
"""

from .connection_manager import (
    ConnectionManager,
    ConnectionStatus,
    MessageType,
    WSConnection,
    WSMessage,
    get_connection_manager,
)
from .events import EventManager, EventType, get_event_manager
from .handlers import (
    handle_chat_message,
    handle_system_notification,
    register_default_handlers,
)

__all__ = [
    # Connection Manager
    "ConnectionManager",
    "WSConnection",
    "WSMessage",
    "MessageType",
    "ConnectionStatus",
    "get_connection_manager",
    # Handlers
    "handle_chat_message",
    "handle_system_notification",
    "register_default_handlers",
    # Events
    "EventManager",
    "EventType",
    "get_event_manager",
]

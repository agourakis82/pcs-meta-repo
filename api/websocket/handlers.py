"""
Sistema H3 - Handlers WebSocket

Handlers específicos para diferentes tipos de eventos WebSocket.
"""

import logging
from typing import Any, Dict, Optional

from .connection_manager import (
    MessageType,
    WSConnection,
    WSMessage,
    get_connection_manager,
)

logger = logging.getLogger(__name__)


async def handle_chat_message(connection: WSConnection, message: WSMessage):
    """Handler para mensagens de chat."""
    try:
        if not connection.user:
            return
        
        # Broadcast para sala se especificada
        if message.room:
            manager = get_connection_manager()
            await manager.broadcast_to_room(
                message.room,
                {
                    "type": "chat",
                    "user": connection.user.username,
                    "message": message.data,
                    "timestamp": message.timestamp.isoformat()
                },
                exclude_connection=connection.id
            )
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")


async def handle_system_notification(connection: WSConnection, message: WSMessage):
    """Handler para notificações do sistema."""
    try:
        # Log da notificação
        logger.info(f"System notification from {connection.id}: {message.data}")
    except Exception as e:
        logger.error(f"Error handling system notification: {e}")


def register_default_handlers():
    """Registra handlers padrão."""
    manager = get_connection_manager()
    manager.register_message_handler(MessageType.TEXT, handle_chat_message)
    manager.register_message_handler(MessageType.JSON, handle_chat_message)
    manager.register_message_handler(MessageType.SYSTEM, handle_system_notification)def register_default_handlers():
    """Registra handlers padrão."""
    manager = get_connection_manager()
    manager.register_message_handler(MessageType.TEXT, handle_chat_message)
    manager.register_message_handler(MessageType.JSON, handle_chat_message)
    manager.register_message_handler(MessageType.SYSTEM, handle_system_notification)
"""
Sistema H3 - Gerenciador de Conexões WebSocket

Gerenciamento de conexões WebSocket com broadcast, rooms, autenticação e rate limiting.
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from fastapi import WebSocket, WebSocketDisconnect

from ..auth import User, get_auth_manager

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Status da conexão WebSocket."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """Tipos de mensagens WebSocket."""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    BROADCAST = "broadcast"
    SYSTEM = "system"


@dataclass
class WSMessage:
    """Mensagem WebSocket."""
    type: MessageType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    sender_id: Optional[str] = None
    room: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "sender_id": self.sender_id,
            "room": self.room,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WSMessage':
        """Cria mensagem a partir de dicionário."""
        return cls(
            type=MessageType(data["type"]),
            data=data["data"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            sender_id=data.get("sender_id"),
            room=data.get("room"),
            metadata=data.get("metadata", {})
        )


@dataclass
class WSConnection:
    """Representação de uma conexão WebSocket."""
    id: str
    websocket: WebSocket
    user: Optional[User] = None
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    rooms: Set[str] = field(default_factory=set)
    message_count: int = 0
    rate_limit_count: int = 0
    rate_limit_reset: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=1))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """Atualiza timestamp da última atividade."""
        self.last_activity = datetime.now()
        self.message_count += 1
    
    def is_rate_limited(self, max_messages_per_minute: int = 60) -> bool:
        """Verifica se conexão está com rate limit."""
        now = datetime.now()
        
        # Reset contador se passou 1 minuto
        if now > self.rate_limit_reset:
            self.rate_limit_count = 0
            self.rate_limit_reset = now + timedelta(minutes=1)
        
        # Verificar limite
        if self.rate_limit_count >= max_messages_per_minute:
            return True
        
        self.rate_limit_count += 1
        return False


class ConnectionManager:
    """Gerenciador de conexões WebSocket."""
    
    def __init__(self):
        self.connections: Dict[str, WSConnection] = {}
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room -> connection_ids
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.auth_manager = get_auth_manager()
        
        # Configurações
        self.max_connections_per_user = 5
        self.max_rooms_per_connection = 10
        self.connection_timeout_minutes = 30
        self.max_messages_per_minute = 60
        self.enable_authentication = True
        
        # Métricas
        self.total_connections = 0
        self.total_messages = 0
        self.connection_history: List[Dict[str, Any]] = []
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> WSConnection:
        """Estabelece nova conexão WebSocket."""
        try:
            await websocket.accept()
            
            connection = WSConnection(
                id=connection_id,
                websocket=websocket,
                status=ConnectionStatus.CONNECTED
            )
            
            self.connections[connection_id] = connection
            self.total_connections += 1
            
            # Registrar na história
            self.connection_history.append({
                "event": "connect",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"WebSocket connection established: {connection_id}")
            
            # Enviar mensagem de boas-vindas
            await self.send_system_message(
                connection_id,
                "Connection established. Please authenticate if required."
            )
            
            return connection
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """Desconecta conexão WebSocket."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            # Remover de todas as salas
            for room in connection.rooms.copy():
                await self.leave_room(connection_id, room)
            
            # Remover das conexões do usuário
            if connection.user:
                self.user_connections[connection.user.id].discard(connection_id)
                if not self.user_connections[connection.user.id]:
                    del self.user_connections[connection.user.id]
            
            # Remover conexão
            connection.status = ConnectionStatus.DISCONNECTED
            del self.connections[connection_id]
            
            # Registrar na história
            self.connection_history.append({
                "event": "disconnect",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"WebSocket connection disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
    
    async def authenticate_connection(self, connection_id: str, token: str) -> bool:
        """Autentica conexão WebSocket."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            # Verificar token
            auth_result = await self.auth_manager.authenticate_token(token)
            if not auth_result.success or not auth_result.user:
                await self.send_system_message(connection_id, "Authentication failed")
                return False
            
            # Verificar limite de conexões por usuário
            user_connection_count = len(self.user_connections[auth_result.user.id])
            if user_connection_count >= self.max_connections_per_user:
                await self.send_system_message(
                    connection_id, 
                    "Maximum connections per user exceeded"
                )
                return False
            
            # Autenticar conexão
            connection.user = auth_result.user
            self.user_connections[auth_result.user.id].add(connection_id)
            
            await self.send_system_message(
                connection_id,
                f"Authenticated as {auth_result.user.username}"
            )
            
            logger.info(f"WebSocket connection authenticated: {connection_id} -> {auth_result.user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating WebSocket connection: {e}")
            return False
    
    async def join_room(self, connection_id: str, room: str) -> bool:
        """Adiciona conexão a uma sala."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            # Verificar autenticação se necessária
            if self.enable_authentication and not connection.user:
                await self.send_system_message(connection_id, "Authentication required to join rooms")
                return False
            
            # Verificar limite de salas por conexão
            if len(connection.rooms) >= self.max_rooms_per_connection:
                await self.send_system_message(connection_id, "Maximum rooms per connection exceeded")
                return False
            
            # Adicionar à sala
            connection.rooms.add(room)
            self.rooms[room].add(connection_id)
            
            await self.send_system_message(connection_id, f"Joined room: {room}")
            
            # Notificar outros na sala
            await self.broadcast_to_room(
                room,
                f"User joined room: {connection.user.username if connection.user else 'Anonymous'}",
                MessageType.SYSTEM,
                exclude_connection=connection_id
            )
            
            logger.info(f"Connection {connection_id} joined room {room}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining room: {e}")
            return False
    
    async def leave_room(self, connection_id: str, room: str) -> bool:
        """Remove conexão de uma sala."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return False
            
            # Remover da sala
            connection.rooms.discard(room)
            self.rooms[room].discard(connection_id)
            
            # Limpar sala vazia
            if not self.rooms[room]:
                del self.rooms[room]
            
            await self.send_system_message(connection_id, f"Left room: {room}")
            
            # Notificar outros na sala
            if room in self.rooms:
                await self.broadcast_to_room(
                    room,
                    f"User left room: {connection.user.username if connection.user else 'Anonymous'}",
                    MessageType.SYSTEM,
                    exclude_connection=connection_id
                )
            
            logger.info(f"Connection {connection_id} left room {room}")
            return True
            
        except Exception as e:
            logger.error(f"Error leaving room: {e}")
            return False
    
    async def send_message(
        self, 
        connection_id: str, 
        message: Union[str, Dict, WSMessage]
    ) -> bool:
        """Envia mensagem para uma conexão específica."""
        try:
            connection = self.connections.get(connection_id)
            if not connection or connection.status != ConnectionStatus.CONNECTED:
                return False
            
            # Converter mensagem se necessário
            if isinstance(message, str):
                message = WSMessage(type=MessageType.TEXT, data=message)
            elif isinstance(message, dict):
                message = WSMessage(type=MessageType.JSON, data=message)
            
            # Verificar rate limit
            if connection.is_rate_limited(self.max_messages_per_minute):
                logger.warning(f"Rate limit exceeded for connection {connection_id}")
                return False
            
            # Enviar mensagem
            await connection.websocket.send_json(message.to_dict())
            connection.update_activity()
            self.total_messages += 1
            
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def send_system_message(self, connection_id: str, message: str) -> bool:
        """Envia mensagem do sistema."""
        system_message = WSMessage(
            type=MessageType.SYSTEM,
            data={"message": message, "sender": "system"}
        )
        return await self.send_message(connection_id, system_message)
    
    async def broadcast_to_room(
        self, 
        room: str, 
        message: Union[str, Dict, WSMessage],
        message_type: MessageType = MessageType.BROADCAST,
        exclude_connection: Optional[str] = None
    ) -> int:
        """Envia mensagem para todos na sala."""
        try:
            if room not in self.rooms:
                return 0
            
            # Converter mensagem se necessário
            if isinstance(message, str):
                message = WSMessage(type=message_type, data=message, room=room)
            elif isinstance(message, dict):
                message = WSMessage(type=message_type, data=message, room=room)
            
            sent_count = 0
            connection_ids = self.rooms[room].copy()
            
            for connection_id in connection_ids:
                if connection_id != exclude_connection:
                    if await self.send_message(connection_id, message):
                        sent_count += 1
            
            logger.info(f"Broadcast to room {room}: {sent_count} messages sent")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting to room: {e}")
            return 0
    
    async def broadcast_to_user(
        self, 
        user_id: str, 
        message: Union[str, Dict, WSMessage]
    ) -> int:
        """Envia mensagem para todas as conexões de um usuário."""
        try:
            if user_id not in self.user_connections:
                return 0
            
            sent_count = 0
            connection_ids = self.user_connections[user_id].copy()
            
            for connection_id in connection_ids:
                if await self.send_message(connection_id, message):
                    sent_count += 1
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting to user: {e}")
            return 0
    
    async def broadcast_to_all(
        self, 
        message: Union[str, Dict, WSMessage]
    ) -> int:
        """Envia mensagem para todas as conexões."""
        try:
            sent_count = 0
            connection_ids = list(self.connections.keys())
            
            for connection_id in connection_ids:
                if await self.send_message(connection_id, message):
                    sent_count += 1
            
            logger.info(f"Broadcast to all: {sent_count} messages sent")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting to all: {e}")
            return 0
    
    async def handle_message(self, connection_id: str, raw_data: str):
        """Processa mensagem recebida."""
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            # Parse da mensagem
            try:
                data = json.loads(raw_data)
                message = WSMessage.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                # Tratar como mensagem de texto simples
                message = WSMessage(type=MessageType.TEXT, data=raw_data)
            
            message.sender_id = connection_id
            connection.update_activity()
            
            # Processar mensagem baseado no tipo
            await self._process_message(connection, message)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_system_message(connection_id, "Error processing message")
    
    async def _process_message(self, connection: WSConnection, message: WSMessage):
        """Processa mensagem baseado no tipo."""
        try:
            if message.type == MessageType.AUTH:
                token = message.data.get("token") if isinstance(message.data, dict) else str(message.data)
                await self.authenticate_connection(connection.id, token)
                
            elif message.type == MessageType.JOIN_ROOM:
                room = message.data.get("room") if isinstance(message.data, dict) else str(message.data)
                await self.join_room(connection.id, room)
                
            elif message.type == MessageType.LEAVE_ROOM:
                room = message.data.get("room") if isinstance(message.data, dict) else str(message.data)
                await self.leave_room(connection.id, room)
                
            elif message.type == MessageType.BROADCAST:
                if message.room:
                    await self.broadcast_to_room(message.room, message.data, exclude_connection=connection.id)
                
            elif message.type == MessageType.PING:
                pong_message = WSMessage(type=MessageType.PONG, data="pong")
                await self.send_message(connection.id, pong_message)
            
            # Executar handlers registrados
            handlers = self.message_handlers.get(message.type, [])
            for handler in handlers:
                try:
                    await handler(connection, message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Registra handler para tipo de mensagem."""
        self.message_handlers[message_type].append(handler)
    
    async def cleanup_inactive_connections(self):
        """Remove conexões inativas."""
        now = datetime.now()
        timeout = timedelta(minutes=self.connection_timeout_minutes)
        inactive_connections = []
        
        for connection_id, connection in self.connections.items():
            if now - connection.last_activity > timeout:
                inactive_connections.append(connection_id)
        
        for connection_id in inactive_connections:
            await self.disconnect(connection_id)
        
        if inactive_connections:
            logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas das conexões."""
        active_connections = len(self.connections)
        authenticated_connections = sum(1 for conn in self.connections.values() if conn.user)
        total_rooms = len(self.rooms)
        
        return {
            "active_connections": active_connections,
            "authenticated_connections": authenticated_connections,
            "anonymous_connections": active_connections - authenticated_connections,
            "total_rooms": total_rooms,
            "total_connections_ever": self.total_connections,
            "total_messages": self.total_messages,
            "rooms": {room: len(connections) for room, connections in self.rooms.items()}
        }
    
    def get_room_info(self, room: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de uma sala."""
        if room not in self.rooms:
            return None
        
        connection_ids = self.rooms[room]
        connections_info = []
        
        for conn_id in connection_ids:
            connection = self.connections.get(conn_id)
            if connection:
                connections_info.append({
                    "connection_id": conn_id,
                    "username": connection.user.username if connection.user else "Anonymous",
                    "connected_at": connection.connected_at.isoformat(),
                    "last_activity": connection.last_activity.isoformat()
                })
        
        return {
            "room": room,
            "connection_count": len(connection_ids),
            "connections": connections_info
        }


# Instância global
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Obtém instância singleton do ConnectionManager."""
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    
    return _connection_manager    return _connection_manager
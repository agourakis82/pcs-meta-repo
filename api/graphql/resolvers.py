"""
GraphQL Resolvers for PCS H3 Integration System
Implements unified GraphQL resolvers for all integrated systems
"""
import asyncio
import os

# Import managers from other H3 systems
import sys
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

import strawberry

from .types import (
    AuthResult,
    CacheStats,
    ConnectionStats,
    CreateApiKeyInput,
    CreateUserInput,
    GatewayInfo,
    LoginInput,
    MetricData,
    OperationResult,
    PaginationInfo,
    Role,
    RouteInfo,
    SystemHealth,
    UpdateUserInput,
    User,
    UserConnection,
    WebSocketMessageInput,
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from auth.auth_manager import AuthManager
    from auth.user_manager import UserManager
    from gateway.config import GatewayConfig
    from gateway.router_manager import RouterManager
    from websocket.connection_manager import ConnectionManager
except ImportError as e:
    print(f"Warning: Could not import H3 managers: {e}")
    # Create mock managers for development
    class MockManager:
        async def get_stats(self): return {}
        async def get_health(self): return {"status": "ok"}
        async def list_users(self, **kwargs): return []
        async def get_user(self, user_id): return None
        async def create_user(self, **kwargs): return None
        async def update_user(self, **kwargs): return None
        async def delete_user(self, user_id): return True
        async def login(self, **kwargs): return {"success": False}
        async def create_api_key(self, **kwargs): return None
        async def list_api_keys(self, user_id): return []
        async def get_cache_stats(self): return {}
        async def get_connection_stats(self): return {}
        async def send_message(self, **kwargs): return True
        async def get_routes(self): return []
        async def get_gateway_info(self): return {}
    
    AuthManager = MockManager
    UserManager = MockManager
    ConnectionManager = MockManager
    RouterManager = MockManager


@strawberry.type
class Query:
    """Root Query type for GraphQL API"""
    
    @strawberry.field
    async def health(self) -> SystemHealth:
        """Get system health status"""
        try:
            # Aggregate health from all systems
            auth_health = await self._get_auth_health()
            cache_health = await self._get_cache_health()
            websocket_health = await self._get_websocket_health()
            gateway_health = await self._get_gateway_health()
            
            overall_status = "healthy"
            if any(h.get("status") != "healthy" for h in [auth_health, cache_health, websocket_health, gateway_health]):
                overall_status = "degraded"
            
            return SystemHealth(
                status=overall_status,
                timestamp=datetime.now(),
                uptime=3600,  # Placeholder
                version="4.4.0",
                components={
                    "auth": auth_health,
                    "cache": cache_health,
                    "websocket": websocket_health,
                    "gateway": gateway_health
                }
            )
        except Exception as e:
            return SystemHealth(
                status="error",
                timestamp=datetime.now(),
                uptime=0,
                version="4.4.0",
                components={"error": str(e)}
            )
    
    @strawberry.field
    async def users(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None
    ) -> UserConnection:
        """Get paginated list of users"""
        try:
            user_manager = UserManager()
            users_data = await user_manager.list_users(
                page=page,
                limit=limit,
                search=search,
                role=role
            )
            
            users = [
                User(
                    id=user.get("id"),
                    username=user.get("username"),
                    email=user.get("email"),
                    first_name=user.get("first_name"),
                    last_name=user.get("last_name"),
                    status=user.get("status"),
                    roles=[Role(
                        id=role.get("id"),
                        name=role.get("name"),
                        description=role.get("description"),
                        permissions=role.get("permissions", []),
                        is_system=role.get("is_system", False)
                    ) for role in user.get("roles", [])],
                    created_at=user.get("created_at", datetime.now()),
                    updated_at=user.get("updated_at", datetime.now()),
                    last_login=user.get("last_login"),
                    full_name=user.get("full_name"),
                    is_active=user.get("is_active", True)
                )
                for user in users_data.get("users", [])
            ]
            
            total_items = users_data.get("total", 0)
            total_pages = (total_items + limit - 1) // limit
            
            pagination = PaginationInfo(
                page=page,
                page_size=limit,
                total_items=total_items,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            return UserConnection(
                users=users,
                pagination=pagination
            )
        except Exception:
            return UserConnection(
                users=[],
                pagination=PaginationInfo(
                    page=page,
                    page_size=limit,
                    total_items=0,
                    total_pages=0,
                    has_next=False,
                    has_previous=False
                )
            )
    
    @strawberry.field
    async def user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_manager = UserManager()
            user_data = await user_manager.get_user(user_id)
            
            if not user_data:
                return None
            
            return User(
                id=user_data.get("id"),
                username=user_data.get("username"),
                email=user_data.get("email"),
                full_name=user_data.get("full_name"),
                is_active=user_data.get("is_active", True),
                created_at=user_data.get("created_at", datetime.now()),
                roles=[Role(name=role) for role in user_data.get("roles", [])]
            )
        except Exception:
            return None
    
    @strawberry.field
    async def cache_stats(self) -> CacheStats:
        """Get cache system statistics"""
        try:
            # Mock cache stats - integrate with actual cache system
            return CacheStats(
                total_keys=1000,
                memory_usage=1048576,  # 1MB
                hit_rate=0.85,
                miss_rate=0.15,
                evictions=50,
                operations_per_second=100.0,
                average_ttl=3600
            )
        except Exception:
            return CacheStats(
                total_keys=0,
                memory_usage=0,
                hit_rate=0.0,
                miss_rate=0.0,
                evictions=0,
                operations_per_second=0.0,
                average_ttl=0
            )
    
    @strawberry.field
    async def connection_stats(self) -> ConnectionStats:
        """Get WebSocket connection statistics"""
        try:
            connection_manager = ConnectionManager()
            stats = await connection_manager.get_connection_stats()
            
            return ConnectionStats(
                active_connections=stats.get("active_connections", 0),
                total_connections=stats.get("total_connections", 0),
                messages_sent=stats.get("messages_sent", 0),
                messages_received=stats.get("messages_received", 0),
                rooms=stats.get("rooms", 0),
                bandwidth_usage=stats.get("bandwidth_usage", 0)
            )
        except Exception:
            return ConnectionStats(
                active_connections=0,
                total_connections=0,
                messages_sent=0,
                messages_received=0,
                rooms=0,
                bandwidth_usage=0
            )
    
    @strawberry.field
    async def gateway_info(self) -> GatewayInfo:
        """Get API Gateway information"""
        try:
            router_manager = RouterManager()
            routes = await router_manager.get_routes()
            
            return GatewayInfo(
                version="1.0.0",
                uptime=3600,
                total_requests=10000,
                active_connections=100,
                routes=[
                    RouteInfo(
                        path=route.get("path"),
                        method=route.get("method"),
                        handler=route.get("handler"),
                        middleware=route.get("middleware", [])
                    )
                    for route in routes
                ]
            )
        except Exception:
            return GatewayInfo(
                version="1.0.0",
                uptime=0,
                total_requests=0,
                active_connections=0,
                routes=[]
            )
    
    @strawberry.field
    async def metrics(self, metric_name: Optional[str] = None) -> List[MetricData]:
        """Get system metrics"""
        try:
            # Mock metrics - integrate with actual monitoring system
            base_metrics = [
                MetricData(
                    name="cpu_usage",
                    value=45.5,
                    timestamp=datetime.now(),
                    labels={"component": "api"}
                ),
                MetricData(
                    name="memory_usage",
                    value=1024.0,
                    timestamp=datetime.now(),
                    labels={"component": "api", "unit": "MB"}
                ),
                MetricData(
                    name="request_rate",
                    value=150.0,
                    timestamp=datetime.now(),
                    labels={"component": "gateway", "unit": "req/s"}
                )
            ]
            
            if metric_name:
                return [m for m in base_metrics if m.name == metric_name]
            return base_metrics
        except Exception:
            return []
    
    async def _get_auth_health(self) -> Dict[str, Any]:
        """Get authentication system health"""
        try:
            auth_manager = AuthManager()
            return await auth_manager.get_health()
        except Exception:
            return {"status": "error", "error": "Auth system unavailable"}
    
    async def _get_cache_health(self) -> Dict[str, Any]:
        """Get cache system health"""
        try:
            # Mock cache health - integrate with actual cache system
            return {"status": "healthy", "connections": 10}
        except Exception:
            return {"status": "error", "error": "Cache system unavailable"}
    
    async def _get_websocket_health(self) -> Dict[str, Any]:
        """Get WebSocket system health"""
        try:
            connection_manager = ConnectionManager()
            return await connection_manager.get_health()
        except Exception:
            return {"status": "error", "error": "WebSocket system unavailable"}
    
    async def _get_gateway_health(self) -> Dict[str, Any]:
        """Get API Gateway health"""
        try:
            # Mock gateway health - integrate with actual gateway system
            return {"status": "healthy", "routes": 25}
        except Exception:
            return {"status": "error", "error": "Gateway system unavailable"}


@strawberry.type
class Mutation:
    """Root Mutation type for GraphQL API"""
    
    @strawberry.mutation
    async def login(self, input: LoginInput) -> AuthResult:
        """Authenticate user and return session"""
        try:
            auth_manager = AuthManager()
            result = await auth_manager.login(
                username=input.username,
                password=input.password
            )
            
            if result.get("success"):
                return AuthResult(
                    success=True,
                    token=result.get("token"),
                    refresh_token=result.get("refresh_token"),
                    expires_at=result.get("expires_at"),
                    user=User(
                        id=result["user"].get("id"),
                        username=result["user"].get("username"),
                        email=result["user"].get("email"),
                        full_name=result["user"].get("full_name"),
                        is_active=result["user"].get("is_active", True),
                        created_at=result["user"].get("created_at", datetime.now()),
                        roles=[Role(name=role) for role in result["user"].get("roles", [])]
                    )
                )
            else:
                return AuthResult(
                    success=False,
                    error=result.get("error", "Invalid credentials")
                )
        except Exception as e:
            return AuthResult(
                success=False,
                error=str(e)
            )
    
    @strawberry.mutation
    async def create_user(self, input: CreateUserInput) -> OperationResult:
        """Create a new user"""
        try:
            user_manager = UserManager()
            user = await user_manager.create_user(
                username=input.username,
                email=input.email,
                password=input.password,
                full_name=input.full_name,
                roles=input.roles
            )
            
            return OperationResult(
                success=True,
                message="User created successfully",
                data={"user_id": user.get("id")}
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    @strawberry.mutation
    async def update_user(self, user_id: str, input: UpdateUserInput) -> OperationResult:
        """Update existing user"""
        try:
            user_manager = UserManager()
            await user_manager.update_user(
                user_id=user_id,
                email=input.email,
                full_name=input.full_name,
                is_active=input.is_active,
                roles=input.roles
            )
            
            return OperationResult(
                success=True,
                message="User updated successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    @strawberry.mutation
    async def delete_user(self, user_id: str) -> OperationResult:
        """Delete user"""
        try:
            user_manager = UserManager()
            await user_manager.delete_user(user_id)
            
            return OperationResult(
                success=True,
                message="User deleted successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    @strawberry.mutation
    async def create_api_key(self, input: CreateApiKeyInput) -> OperationResult:
        """Create API key for user"""
        try:
            auth_manager = AuthManager()
            api_key = await auth_manager.create_api_key(
                user_id=input.user_id,
                name=input.name,
                permissions=input.permissions,
                expires_at=input.expires_at
            )
            
            return OperationResult(
                success=True,
                message="API key created successfully",
                data={"api_key": api_key.get("key")}
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    @strawberry.mutation
    async def send_websocket_message(self, input: WebSocketMessageInput) -> OperationResult:
        """Send WebSocket message"""
        try:
            connection_manager = ConnectionManager()
            await connection_manager.send_message(
                room=input.room,
                message=input.message,
                message_type=input.message_type,
                user_id=input.user_id
            )
            
            return OperationResult(
                success=True,
                message="Message sent successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    @strawberry.mutation
    async def clear_cache(self, pattern: Optional[str] = None) -> OperationResult:
        """Clear cache entries"""
        try:
            # Mock cache clear - integrate with actual cache system
            return OperationResult(
                success=True,
                message=f"Cache cleared{' for pattern: ' + pattern if pattern else ''}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=str(e)
            )


@strawberry.type
class Subscription:
    """Root Subscription type for GraphQL API"""
    
    @strawberry.subscription
    async def system_events(self) -> AsyncGenerator[str, None]:
        """Subscribe to system events"""
        try:
            while True:
                # Mock system events - integrate with actual event system
                await asyncio.sleep(5)
                yield f"System event at {datetime.now().isoformat()}"
        except Exception:
            yield "Subscription error"
    
    @strawberry.subscription
    async def metrics_stream(self, metric_name: str) -> AsyncGenerator[MetricData, None]:
        """Subscribe to real-time metrics"""
        try:
            while True:
                await asyncio.sleep(1)
                yield MetricData(
                    name=metric_name,
                    value=50.0 + (datetime.now().second % 30),  # Mock varying value
                    timestamp=datetime.now(),
                    labels={"component": "live"}
                )
        except Exception:
            yield MetricData(
                name=metric_name,
                value=0.0,
                timestamp=datetime.now(),
                labels={"error": "stream_error"}
            )
    
    @strawberry.subscription
    async def websocket_events(self, room: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Subscribe to WebSocket events"""
        try:
            connection_manager = ConnectionManager()
            async for event in connection_manager.subscribe_to_events(room):
                yield event
        except Exception:
            yield "WebSocket subscription error"                value=0.0,
                timestamp=datetime.now(),
                labels={"error": "stream_error"}
            )
    
    @strawberry.subscription
    async def websocket_events(self, room: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Subscribe to WebSocket events"""
        try:
            connection_manager = ConnectionManager()
            async for event in connection_manager.subscribe_to_events(room):
                yield event
        except Exception:
            yield "WebSocket subscription error"
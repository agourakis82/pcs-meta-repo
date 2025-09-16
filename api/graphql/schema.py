"""
GraphQL Schema for PCS H3 Integration System
Main schema file that combines all GraphQL types and resolvers
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import strawberry


# Define GraphQL types using strawberry syntax
@strawberry.type
class SimpleUser:
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True


@strawberry.type  
class SimpleRole:
    id: str
    name: str
    description: Optional[str] = None


@strawberry.type
class SimpleSystemHealth:
    status: str
    timestamp: datetime
    uptime: int
    version: str
    components: Optional[str] = None


@strawberry.type
class SimpleCacheStats:
    total_keys: int
    memory_usage: int
    hit_rate: float
    miss_rate: float


@strawberry.type
class SimpleConnectionStats:
    active_connections: int
    total_connections: int
    messages_sent: int
    messages_received: int


@strawberry.type
class SimpleMetricData:
    name: str
    value: float
    timestamp: datetime
    labels: Optional[str] = None


@strawberry.type
class SimpleGatewayInfo:
    version: str
    uptime: int
    total_requests: int
    active_connections: int


@strawberry.type
class SimpleRouteInfo:
    path: str
    method: str
    handler: str
    middleware: List[str]


@strawberry.input
class LoginInput:
    username: str
    password: str


@strawberry.input
class CreateUserInput:
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


@strawberry.type
class AuthResult:
    success: bool
    token: Optional[str] = None
    user: Optional[SimpleUser] = None
    error: Optional[str] = None


@strawberry.type
class OperationResult:
    success: bool
    message: str
    data: Optional[str] = None


# Helper functions to create instances
def create_user(id: str, username: str, email: str, 
               full_name: Optional[str] = None, is_active: bool = True) -> SimpleUser:
    user = SimpleUser.__new__(SimpleUser)
    user.id = id
    user.username = username
    user.email = email
    user.full_name = full_name
    user.is_active = is_active
    return user


def create_health(status: str, timestamp: datetime, uptime: int,
                 version: str, components: Optional[str] = None) -> SimpleSystemHealth:
    health = SimpleSystemHealth.__new__(SimpleSystemHealth)
    health.status = status
    health.timestamp = timestamp
    health.uptime = uptime
    health.version = version
    health.components = components
    return health


def create_cache_stats(total_keys: int, memory_usage: int,
                      hit_rate: float, miss_rate: float) -> SimpleCacheStats:
    stats = SimpleCacheStats.__new__(SimpleCacheStats)
    stats.total_keys = total_keys
    stats.memory_usage = memory_usage
    stats.hit_rate = hit_rate
    stats.miss_rate = miss_rate
    return stats


def create_connection_stats(active: int, total: int, sent: int, received: int) -> SimpleConnectionStats:
    stats = SimpleConnectionStats.__new__(SimpleConnectionStats)
    stats.active_connections = active
    stats.total_connections = total
    stats.messages_sent = sent
    stats.messages_received = received
    return stats


def create_gateway_info(version: str, uptime: int, total_requests: int, active_connections: int) -> SimpleGatewayInfo:
    info = SimpleGatewayInfo.__new__(SimpleGatewayInfo)
    info.version = version
    info.uptime = uptime
    info.total_requests = total_requests
    info.active_connections = active_connections
    return info


def create_route_info(path: str, method: str, handler: str, middleware: List[str]) -> SimpleRouteInfo:
    route = SimpleRouteInfo.__new__(SimpleRouteInfo)
    route.path = path
    route.method = method
    route.handler = handler
    route.middleware = middleware
    return route


def create_metric_data(name: str, value: float, timestamp: datetime, labels: Optional[str] = None) -> SimpleMetricData:
    metric = SimpleMetricData.__new__(SimpleMetricData)
    metric.name = name
    metric.value = value
    metric.timestamp = timestamp
    metric.labels = labels
    return metric


def create_auth_result(success: bool, token: Optional[str] = None, 
                      user: Optional[SimpleUser] = None, error: Optional[str] = None) -> AuthResult:
    result = AuthResult.__new__(AuthResult)
    result.success = success
    result.token = token
    result.user = user
    result.error = error
    return result


def create_operation_result(success: bool, message: str, data: Optional[str] = None) -> OperationResult:
    result = OperationResult.__new__(OperationResult)
    result.success = success
    result.message = message
    result.data = data
    return result


@strawberry.type
class Query:
    """Root Query type for GraphQL API"""
    
    @strawberry.field
    def hello(self) -> str:
        """Simple hello world query"""
        return "Hello from PCS H3 GraphQL API!"
    
    @strawberry.field
    async def health(self) -> SimpleSystemHealth:
        """Get system health status"""
        return create_health(
            status="healthy",
            timestamp=datetime.now(),
            uptime=3600,
            version="4.4.0",
            components="all systems operational"
        )
    
    @strawberry.field
    async def users(self, limit: int = 10) -> List[SimpleUser]:
        """Get list of users"""
        # Mock users for now
        users = [
            create_user(
                id="1",
                username="admin",
                email="admin@pcs.edu",
                full_name="System Administrator",
                is_active=True
            ),
            create_user(
                id="2", 
                username="user1",
                email="user1@pcs.edu",
                full_name="Test User",
                is_active=True
            )
        ]
        return users[:limit]
    
    @strawberry.field
    async def user(self, user_id: str) -> Optional[SimpleUser]:
        """Get user by ID"""
        if user_id == "1":
            return create_user(
                id="1",
                username="admin",
                email="admin@pcs.edu",
                full_name="System Administrator",
                is_active=True
            )
        return None
    
    @strawberry.field
    async def cache_stats(self) -> SimpleCacheStats:
        """Get cache system statistics"""
        return create_cache_stats(
            total_keys=1000,
            memory_usage=1048576,  # 1MB
            hit_rate=0.85,
            miss_rate=0.15
        )
    
    @strawberry.field
    async def connection_stats(self) -> SimpleConnectionStats:
        """Get WebSocket connection statistics"""
        return create_connection_stats(
            active=25,
            total=150,
            sent=5000,
            received=4800
        )
    
    @strawberry.field
    async def gateway_info(self) -> SimpleGatewayInfo:
        """Get API Gateway information"""
        return create_gateway_info(
            version="1.0.0",
            uptime=3600,
            total_requests=10000,
            active_connections=100
        )
    
    @strawberry.field
    async def routes(self) -> List[SimpleRouteInfo]:
        """Get available routes"""
        return [
            create_route_info(
                path="/api/v1/users",
                method="GET",
                handler="get_users",
                middleware=["auth", "rate_limit"]
            ),
            create_route_info(
                path="/api/v1/auth/login",
                method="POST", 
                handler="login",
                middleware=["rate_limit"]
            )
        ]
    
    @strawberry.field
    async def metrics(self, metric_name: Optional[str] = None) -> List[SimpleMetricData]:
        """Get system metrics"""
        base_metrics = [
            create_metric_data(
                name="cpu_usage",
                value=45.5,
                timestamp=datetime.now(),
                labels="component=api"
            ),
            create_metric_data(
                name="memory_usage",
                value=1024.0,
                timestamp=datetime.now(),
                labels="component=api,unit=MB"
            ),
            create_metric_data(
                name="request_rate",
                value=150.0,
                timestamp=datetime.now(),
                labels="component=gateway,unit=req/s"
            )
        ]
        
        if metric_name:
            return [m for m in base_metrics if m.name == metric_name]
        return base_metrics


@strawberry.type
class Mutation:
    """Root Mutation type for GraphQL API"""
    
    @strawberry.mutation
    async def login(self, input: LoginInput) -> AuthResult:
        """Authenticate user and return session"""
        # Mock authentication
        if input.username == "admin" and input.password == "admin":
            return create_auth_result(
                success=True,
                token="mock-jwt-token-12345",
                user=create_user(
                    id="1",
                    username="admin", 
                    email="admin@pcs.edu",
                    full_name="System Administrator",
                    is_active=True
                )
            )
        else:
            return create_auth_result(
                success=False,
                error="Invalid credentials"
            )
    
    @strawberry.mutation
    async def create_user(self, input: CreateUserInput) -> OperationResult:
        """Create a new user"""
        # Mock user creation
        return create_operation_result(
            success=True,
            message=f"User {input.username} created successfully",
            data=f"user_id=mock-{input.username}"
        )
    
    @strawberry.mutation
    async def clear_cache(self, pattern: Optional[str] = None) -> OperationResult:
        """Clear cache entries"""
        message = "Cache cleared"
        if pattern:
            message += f" for pattern: {pattern}"
        
        return create_operation_result(
            success=True,
            message=message
        )


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)    mutation=Mutation
)
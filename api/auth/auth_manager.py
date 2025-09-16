"""
Sistema H3 - Gerenciador de Autenticação

Sistema completo de autenticação com JWT, OAuth2, API keys e gestão de usuários.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .jwt_handler import JWTHandler
from .permissions import Permission, PermissionManager, Role
from .user_manager import User, UserManager

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Métodos de autenticação suportados."""

    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class SessionStatus(Enum):
    """Status da sessão."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


@dataclass
class AuthConfig:
    """Configuração do sistema de autenticação."""

    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key_expire_days: int = 365
    max_sessions_per_user: int = 5
    password_min_length: int = 8
    require_password_complexity: bool = True
    enable_2fa: bool = False
    session_timeout_minutes: int = 60


@dataclass
class AuthSession:
    """Sessão de autenticação."""

    session_id: str
    user_id: str
    method: AuthMethod
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus
    metadata: Dict[str, Any]


@dataclass
class AuthResult:
    """Resultado de autenticação."""

    success: bool
    user: Optional[User] = None
    session: Optional[AuthSession] = None
    tokens: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    requires_2fa: bool = False


class AuthManager:
    """Gerenciador principal de autenticação."""

    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig()
        self.jwt_handler = JWTHandler(
            secret_key=self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )
        self.user_manager = UserManager()
        self.permission_manager = PermissionManager()

        # Armazenamento em memória das sessões (em produção usar Redis)
        self.active_sessions: Dict[str, AuthSession] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        self.api_keys: Dict[str, Dict[str, Any]] = {}

    async def authenticate_user(
        self, username: str, password: str, method: AuthMethod = AuthMethod.JWT
    ) -> AuthResult:
        """Autentica usuário com username/password."""
        try:
            # Verificar credenciais
            user = await self.user_manager.authenticate(username, password)
            if not user:
                return AuthResult(success=False, error="Invalid credentials")

            # Verificar se usuário está ativo
            if not user.is_active:
                return AuthResult(success=False, error="Account is deactivated")

            # Verificar 2FA se habilitado
            if self.config.enable_2fa and user.two_factor_enabled:
                return AuthResult(success=False, requires_2fa=True, user=user)

            # Criar sessão
            session = await self._create_session(user, method)

            # Gerar tokens se necessário
            tokens = None
            if method == AuthMethod.JWT:
                tokens = await self._generate_tokens(user, session)

            return AuthResult(success=True, user=user, session=session, tokens=tokens)

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult(success=False, error="Authentication failed")

    async def authenticate_token(self, token: str) -> AuthResult:
        """Autentica usando JWT token."""
        try:
            # Verificar token
            payload = await self.jwt_handler.verify_token(token)
            if not payload:
                return AuthResult(success=False, error="Invalid token")

            user_id = payload.get("sub")
            session_id = payload.get("session_id")

            # Verificar usuário
            user = await self.user_manager.get_user_by_id(user_id)
            if not user or not user.is_active:
                return AuthResult(success=False, error="User not found or inactive")

            # Verificar sessão
            session = self.active_sessions.get(session_id)
            if not session or session.status != SessionStatus.ACTIVE:
                return AuthResult(success=False, error="Session invalid or expired")

            # Atualizar última atividade
            session.last_activity = datetime.now()

            return AuthResult(success=True, user=user, session=session)

        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return AuthResult(success=False, error="Token authentication failed")

    async def authenticate_api_key(self, api_key: str) -> AuthResult:
        """Autentica usando API key."""
        try:
            # Verificar API key
            key_data = self.api_keys.get(api_key)
            if not key_data:
                return AuthResult(success=False, error="Invalid API key")

            # Verificar expiração
            if datetime.now() > key_data["expires_at"]:
                return AuthResult(success=False, error="API key expired")

            # Verificar usuário
            user = await self.user_manager.get_user_by_id(key_data["user_id"])
            if not user or not user.is_active:
                return AuthResult(success=False, error="User not found or inactive")

            # Criar sessão temporária
            session = await self._create_session(user, AuthMethod.API_KEY)

            return AuthResult(success=True, user=user, session=session)

        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return AuthResult(success=False, error="API key authentication failed")

    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Renova access token usando refresh token."""
        try:
            # Verificar refresh token
            payload = await self.jwt_handler.verify_refresh_token(refresh_token)
            if not payload:
                return AuthResult(success=False, error="Invalid refresh token")

            user_id = payload.get("sub")
            session_id = payload.get("session_id")

            # Verificar usuário e sessão
            user = await self.user_manager.get_user_by_id(user_id)
            session = self.active_sessions.get(session_id)

            if not user or not session or session.status != SessionStatus.ACTIVE:
                return AuthResult(success=False, error="Invalid session")

            # Gerar novos tokens
            tokens = await self._generate_tokens(user, session)

            return AuthResult(success=True, user=user, session=session, tokens=tokens)

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthResult(success=False, error="Token refresh failed")

    async def logout(self, session_id: str) -> bool:
        """Faz logout de uma sessão."""
        try:
            session = self.active_sessions.get(session_id)
            if session:
                session.status = SessionStatus.REVOKED
                await self._cleanup_session(session_id)
                return True
            return False

        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    async def logout_all_sessions(self, user_id: str) -> bool:
        """Faz logout de todas as sessões do usuário."""
        try:
            session_ids = self.user_sessions.get(user_id, [])
            for session_id in session_ids:
                await self.logout(session_id)
            return True

        except Exception as e:
            logger.error(f"Logout all sessions error: {e}")
            return False

    async def create_api_key(
        self, user_id: str, name: str = "Default API Key", permissions: List[str] = None
    ) -> Optional[str]:
        """Cria uma nova API key."""
        try:
            # Gerar API key
            api_key = self._generate_api_key(user_id, name)

            # Armazenar metadados
            self.api_keys[api_key] = {
                "user_id": user_id,
                "name": name,
                "created_at": datetime.now(),
                "expires_at": datetime.now()
                + timedelta(days=self.config.api_key_expire_days),
                "permissions": permissions or [],
                "last_used": None,
            }

            logger.info(f"API key created for user {user_id}")
            return api_key

        except Exception as e:
            logger.error(f"API key creation error: {e}")
            return None

    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoga uma API key."""
        try:
            if api_key in self.api_keys:
                del self.api_keys[api_key]
                return True
            return False

        except Exception as e:
            logger.error(f"API key revocation error: {e}")
            return False

    async def check_permission(self, user: User, permission: str) -> bool:
        """Verifica se usuário tem permissão."""
        return await self.permission_manager.check_permission(user, permission)

    async def get_user_sessions(self, user_id: str) -> List[AuthSession]:
        """Obtém todas as sessões ativas do usuário."""
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []

        for session_id in session_ids:
            session = self.active_sessions.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                sessions.append(session)

        return sessions

    async def cleanup_expired_sessions(self):
        """Remove sessões expiradas."""
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if (
                session.expires_at < now
                or session.last_activity
                + timedelta(minutes=self.config.session_timeout_minutes)
                < now
            ):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            await self._cleanup_session(session_id)

        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    async def _create_session(self, user: User, method: AuthMethod) -> AuthSession:
        """Cria uma nova sessão."""
        session_id = self._generate_session_id(user.id, method)
        now = datetime.now()

        session = AuthSession(
            session_id=session_id,
            user_id=user.id,
            method=method,
            created_at=now,
            last_activity=now,
            expires_at=now + timedelta(minutes=self.config.access_token_expire_minutes),
            status=SessionStatus.ACTIVE,
            metadata={},
        )

        # Armazenar sessão
        self.active_sessions[session_id] = session

        # Associar ao usuário
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = []
        self.user_sessions[user.id].append(session_id)

        # Limitar número de sessões por usuário
        await self._enforce_session_limit(user.id)

        return session

    async def _generate_tokens(
        self, user: User, session: AuthSession
    ) -> Dict[str, str]:
        """Gera tokens JWT."""
        # Access token
        access_token = await self.jwt_handler.create_access_token(
            {
                "sub": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.name for role in user.roles],
                "session_id": session.session_id,
            }
        )

        # Refresh token
        refresh_token = await self.jwt_handler.create_refresh_token(
            {"sub": user.id, "session_id": session.session_id}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.config.access_token_expire_minutes * 60,
        }

    def _generate_session_id(self, user_id: str, method: AuthMethod) -> str:
        """Gera ID único para sessão."""
        data = f"{user_id}{method.value}{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _generate_api_key(self, user_id: str, name: str) -> str:
        """Gera API key única."""
        data = f"{user_id}{name}{datetime.now().isoformat()}"
        return f"pcs_{''.join(data.split())}"[:40]

    async def _enforce_session_limit(self, user_id: str):
        """Aplica limite de sessões por usuário."""
        session_ids = self.user_sessions.get(user_id, [])

        if len(session_ids) > self.config.max_sessions_per_user:
            # Remover sessões mais antigas
            sessions_with_time = []
            for sid in session_ids:
                session = self.active_sessions.get(sid)
                if session:
                    sessions_with_time.append((sid, session.created_at))

            # Ordenar por data de criação
            sessions_with_time.sort(key=lambda x: x[1])

            # Remover as mais antigas
            excess_count = len(session_ids) - self.config.max_sessions_per_user
            for i in range(excess_count):
                session_id = sessions_with_time[i][0]
                await self._cleanup_session(session_id)

    async def _cleanup_session(self, session_id: str):
        """Remove sessão do armazenamento."""
        session = self.active_sessions.get(session_id)
        if session:
            # Remover da lista do usuário
            user_sessions = self.user_sessions.get(session.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)

            # Remover sessão
            del self.active_sessions[session_id]


# Instância global
_auth_manager: Optional[AuthManager] = None


def get_auth_manager(config: Optional[AuthConfig] = None) -> AuthManager:
    """Obtém instância singleton do AuthManager."""
    global _auth_manager

    if _auth_manager is None:
        _auth_manager = AuthManager(config)

    return _auth_manager

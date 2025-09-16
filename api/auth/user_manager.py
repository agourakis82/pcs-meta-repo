"""
Sistema H3 - Gerenciador de Usuários

Gerenciamento de usuários, roles e autenticação básica.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UserStatus(Enum):
    """Status do usuário."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class Role:
    """Representação de um role/função."""

    id: str
    name: str
    description: str = ""
    permissions: List[str] = field(default_factory=list)
    is_system: bool = False


@dataclass
class User:
    """Representação de um usuário."""

    id: str
    username: str
    email: str
    password_hash: str
    first_name: str = ""
    last_name: str = ""
    status: UserStatus = UserStatus.ACTIVE
    roles: List[Role] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    max_login_attempts: int = 5
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se usuário está ativo."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        """Verifica se usuário está bloqueado por tentativas de login."""
        return self.login_attempts >= self.max_login_attempts

    @property
    def full_name(self) -> str:
        """Nome completo do usuário."""
        return f"{self.first_name} {self.last_name}".strip()

    def has_role(self, role_name: str) -> bool:
        """Verifica se usuário tem um role específico."""
        return any(role.name == role_name for role in self.roles)

    def get_permissions(self) -> List[str]:
        """Obtém todas as permissões do usuário."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)
        return list(permissions)


class UserManager:
    """Gerenciador de usuários."""

    def __init__(self):
        # Armazenamento em memória (em produção usar banco de dados)
        self.users: Dict[str, User] = {}
        self.users_by_username: Dict[str, str] = {}  # username -> user_id
        self.users_by_email: Dict[str, str] = {}  # email -> user_id
        self.roles: Dict[str, Role] = {}

        # Inicializar roles padrão
        self._init_default_roles()

        # Criar usuário admin padrão
        self._create_default_admin()

    def _init_default_roles(self):
        """Inicializa roles padrão do sistema."""
        default_roles = [
            Role(
                id="admin",
                name="admin",
                description="Administrador do sistema",
                permissions=[
                    "users:read",
                    "users:write",
                    "users:delete",
                    "roles:read",
                    "roles:write",
                    "roles:delete",
                    "system:admin",
                    "api:full_access",
                ],
                is_system=True,
            ),
            Role(
                id="user",
                name="user",
                description="Usuário padrão",
                permissions=["profile:read", "profile:write", "api:basic_access"],
                is_system=True,
            ),
            Role(
                id="readonly",
                name="readonly",
                description="Acesso somente leitura",
                permissions=["api:read_access"],
                is_system=True,
            ),
        ]

        for role in default_roles:
            self.roles[role.id] = role

    def _create_default_admin(self):
        """Cria usuário admin padrão."""
        admin_user = User(
            id="admin",
            username="admin",
            email="admin@pcs-meta-repo.local",
            password_hash=self._hash_password("admin123"),
            first_name="System",
            last_name="Administrator",
            status=UserStatus.ACTIVE,
            roles=[self.roles["admin"]],
        )

        self.users[admin_user.id] = admin_user
        self.users_by_username[admin_user.username] = admin_user.id
        self.users_by_email[admin_user.email] = admin_user.id

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        roles: List[str] = None,
    ) -> Optional[User]:
        """Cria um novo usuário."""
        try:
            # Verificar se username já existe
            if username in self.users_by_username:
                logger.warning(f"Username '{username}' already exists")
                return None

            # Verificar se email já existe
            if email in self.users_by_email:
                logger.warning(f"Email '{email}' already exists")
                return None

            # Gerar ID único
            user_id = self._generate_user_id(username)

            # Criar usuário
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=self._hash_password(password),
                first_name=first_name,
                last_name=last_name,
                roles=self._get_roles_by_names(roles or ["user"]),
            )

            # Armazenar usuário
            self.users[user_id] = user
            self.users_by_username[username] = user_id
            self.users_by_email[email] = user_id

            logger.info(f"User '{username}' created successfully")
            return user

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Autentica usuário com username/password."""
        try:
            # Buscar usuário
            user = await self.get_user_by_username(username)
            if not user:
                return None

            # Verificar se usuário não está bloqueado
            if user.is_locked:
                logger.warning(
                    f"User '{username}' is locked due to failed login attempts"
                )
                return None

            # Verificar senha
            if not self._verify_password(password, user.password_hash):
                # Incrementar tentativas de login
                user.login_attempts += 1
                user.updated_at = datetime.now()
                logger.warning(
                    f"Invalid password for user '{username}'. Attempts: {user.login_attempts}"
                )
                return None

            # Login bem-sucedido
            user.login_attempts = 0
            user.last_login = datetime.now()
            user.updated_at = datetime.now()

            logger.info(f"User '{username}' authenticated successfully")
            return user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Obtém usuário por ID."""
        return self.users.get(user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtém usuário por username."""
        user_id = self.users_by_username.get(username)
        if user_id:
            return self.users.get(user_id)
        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtém usuário por email."""
        user_id = self.users_by_email.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Atualiza dados do usuário."""
        try:
            user = self.users.get(user_id)
            if not user:
                return None

            # Campos que podem ser atualizados
            updatable_fields = [
                "first_name",
                "last_name",
                "email",
                "status",
                "two_factor_enabled",
                "metadata",
            ]

            for field, value in kwargs.items():
                if field in updatable_fields:
                    setattr(user, field, value)

            user.updated_at = datetime.now()

            # Atualizar índices se necessário
            if "email" in kwargs:
                # Remove old email mapping
                old_email = None
                for email, uid in self.users_by_email.items():
                    if uid == user_id:
                        old_email = email
                        break

                if old_email:
                    del self.users_by_email[old_email]

                # Add new email mapping
                self.users_by_email[kwargs["email"]] = user_id

            logger.info(f"User '{user.username}' updated successfully")
            return user

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None

    async def delete_user(self, user_id: str) -> bool:
        """Remove usuário."""
        try:
            user = self.users.get(user_id)
            if not user:
                return False

            # Remover dos índices
            del self.users_by_username[user.username]
            del self.users_by_email[user.email]
            del self.users[user_id]

            logger.info(f"User '{user.username}' deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """Altera senha do usuário."""
        try:
            user = self.users.get(user_id)
            if not user:
                return False

            # Verificar senha atual
            if not self._verify_password(old_password, user.password_hash):
                return False

            # Atualizar senha
            user.password_hash = self._hash_password(new_password)
            user.updated_at = datetime.now()

            logger.info(f"Password changed for user '{user.username}'")
            return True

        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False

    async def reset_login_attempts(self, user_id: str) -> bool:
        """Reseta tentativas de login do usuário."""
        try:
            user = self.users.get(user_id)
            if not user:
                return False

            user.login_attempts = 0
            user.updated_at = datetime.now()

            logger.info(f"Login attempts reset for user '{user.username}'")
            return True

        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")
            return False

    async def list_users(self, status: UserStatus = None) -> List[User]:
        """Lista usuários."""
        users = list(self.users.values())

        if status:
            users = [user for user in users if user.status == status]

        return users

    def create_role(
        self, name: str, description: str = "", permissions: List[str] = None
    ) -> Optional[Role]:
        """Cria um novo role."""
        try:
            role_id = name.lower().replace(" ", "_")

            if role_id in self.roles:
                logger.warning(f"Role '{name}' already exists")
                return None

            role = Role(
                id=role_id,
                name=name,
                description=description,
                permissions=permissions or [],
            )

            self.roles[role_id] = role

            logger.info(f"Role '{name}' created successfully")
            return role

        except Exception as e:
            logger.error(f"Error creating role: {e}")
            return None

    def get_role(self, role_id: str) -> Optional[Role]:
        """Obtém role por ID."""
        return self.roles.get(role_id)

    def list_roles(self) -> List[Role]:
        """Lista todos os roles."""
        return list(self.roles.values())

    def _get_roles_by_names(self, role_names: List[str]) -> List[Role]:
        """Obtém roles por nomes."""
        roles = []
        for name in role_names:
            role = self.roles.get(name)
            if role:
                roles.append(role)
        return roles

    def _generate_user_id(self, username: str) -> str:
        """Gera ID único para usuário."""
        timestamp = datetime.now().isoformat()
        data = f"{username}{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _hash_password(self, password: str) -> str:
        """Gera hash da senha."""
        # Em produção, usar bcrypt ou argon2
        salt = "pcs-meta-repo-salt"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica senha contra hash."""
        return self._hash_password(password) == password_hash

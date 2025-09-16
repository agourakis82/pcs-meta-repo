"""
Sistema H3 - Gerenciador de Permissões

Sistema de permissões baseado em roles e recursos.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

from .user_manager import Role, User

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Níveis de permissão."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(Enum):
    """Tipos de recursos."""
    USER = "user"
    ROLE = "role"
    API = "api"
    SYSTEM = "system"
    DATA = "data"
    CACHE = "cache"
    MONITORING = "monitoring"


@dataclass
class Permission:
    """Representação de uma permissão."""
    resource: ResourceType
    action: PermissionLevel
    conditions: Optional[Dict[str, any]] = None
    
    def __str__(self) -> str:
        """String representation da permissão."""
        return f"{self.resource.value}:{self.action.value}"
    
    @classmethod
    def from_string(cls, permission_str: str) -> 'Permission':
        """Cria permissão a partir de string."""
        parts = permission_str.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid permission format: {permission_str}")
        
        resource = ResourceType(parts[0])
        action = PermissionLevel(parts[1])
        
        return cls(resource=resource, action=action)


class PermissionManager:
    """Gerenciador de permissões."""
    
    def __init__(self):
        # Mapeamento de permissões do sistema
        self.system_permissions: Dict[str, Permission] = {}
        self._init_system_permissions()
        
        # Cache de permissões por usuário
        self.user_permission_cache: Dict[str, Set[str]] = {}
    
    def _init_system_permissions(self):
        """Inicializa permissões do sistema."""
        permissions = [
            # Permissões de usuários
            "user:read", "user:write", "user:delete", "user:admin",
            
            # Permissões de roles
            "role:read", "role:write", "role:delete", "role:admin",
            
            # Permissões de API
            "api:read", "api:write", "api:admin", "api:full_access", "api:basic_access",
            
            # Permissões de sistema
            "system:read", "system:write", "system:admin",
            
            # Permissões de dados
            "data:read", "data:write", "data:delete", "data:admin",
            
            # Permissões de cache
            "cache:read", "cache:write", "cache:delete", "cache:admin",
            
            # Permissões de monitoramento
            "monitoring:read", "monitoring:write", "monitoring:admin"
        ]
        
        for perm_str in permissions:
            try:
                permission = Permission.from_string(perm_str)
                self.system_permissions[perm_str] = permission
            except ValueError as e:
                logger.error(f"Error initializing permission {perm_str}: {e}")
    
    async def check_permission(self, user: User, permission: str) -> bool:
        """Verifica se usuário tem permissão específica."""
        try:
            # Verificar se usuário está ativo
            if not user.is_active:
                return False
            
            # Usar cache se disponível
            user_permissions = self.user_permission_cache.get(user.id)
            if user_permissions is None:
                user_permissions = self._calculate_user_permissions(user)
                self.user_permission_cache[user.id] = user_permissions
            
            # Verificar permissão específica
            if permission in user_permissions:
                return True
            
            # Verificar permissões hierárquicas
            return self._check_hierarchical_permission(user_permissions, permission)
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def check_multiple_permissions(
        self, 
        user: User, 
        permissions: List[str],
        require_all: bool = True
    ) -> bool:
        """Verifica múltiplas permissões."""
        results = []
        
        for permission in permissions:
            result = await self.check_permission(user, permission)
            results.append(result)
        
        if require_all:
            return all(results)
        else:
            return any(results)
    
    async def get_user_permissions(self, user: User) -> List[str]:
        """Obtém todas as permissões do usuário."""
        try:
            # Usar cache se disponível
            user_permissions = self.user_permission_cache.get(user.id)
            if user_permissions is None:
                user_permissions = self._calculate_user_permissions(user)
                self.user_permission_cache[user.id] = user_permissions
            
            return list(user_permissions)
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []
    
    async def grant_permission_to_role(self, role: Role, permission: str) -> bool:
        """Concede permissão a um role."""
        try:
            if permission in self.system_permissions:
                if permission not in role.permissions:
                    role.permissions.append(permission)
                    self._invalidate_cache()
                    logger.info(f"Permission '{permission}' granted to role '{role.name}'")
                    return True
            else:
                logger.warning(f"Unknown permission: {permission}")
                return False
                
        except Exception as e:
            logger.error(f"Error granting permission: {e}")
            return False
    
    async def revoke_permission_from_role(self, role: Role, permission: str) -> bool:
        """Revoga permissão de um role."""
        try:
            if permission in role.permissions:
                role.permissions.remove(permission)
                self._invalidate_cache()
                logger.info(f"Permission '{permission}' revoked from role '{role.name}'")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error revoking permission: {e}")
            return False
    
    def _calculate_user_permissions(self, user: User) -> Set[str]:
        """Calcula todas as permissões do usuário."""
        permissions = set()
        
        for role in user.roles:
            permissions.update(role.permissions)
        
        return permissions
    
    def _check_hierarchical_permission(
        self, 
        user_permissions: Set[str], 
        required_permission: str
    ) -> bool:
        """Verifica permissões hierárquicas."""
        try:
            resource, action = required_permission.split(":")
            
            # Verificar se tem permissão admin para o recurso
            admin_permission = f"{resource}:admin"
            if admin_permission in user_permissions:
                return True
            
            # Verificar hierarquia de ações
            action_hierarchy = {
                "read": [],
                "write": ["read"],
                "delete": ["read", "write"],
                "admin": ["read", "write", "delete"]
            }
            
            if action in action_hierarchy:
                for lower_action in action_hierarchy[action]:
                    lower_permission = f"{resource}:{lower_action}"
                    if lower_permission in user_permissions:
                        continue
                    else:
                        return False
                return True
            
            return False
            
        except Exception:
            return False
    
    def _invalidate_cache(self):
        """Invalida cache de permissões."""
        self.user_permission_cache.clear()
    
    def create_custom_permission(
        self, 
        resource: str, 
        action: str,
        description: str = ""
    ) -> bool:
        """Cria permissão customizada."""
        try:
            permission_str = f"{resource}:{action}"
            
            if permission_str in self.system_permissions:
                logger.warning(f"Permission already exists: {permission_str}")
                return False
            
            # Verificar se resource e action são válidos
            try:
                resource_type = ResourceType(resource)
                action_level = PermissionLevel(action)
            except ValueError:
                logger.error(f"Invalid resource or action: {resource}:{action}")
                return False
            
            permission = Permission(resource=resource_type, action=action_level)
            self.system_permissions[permission_str] = permission
            
            logger.info(f"Custom permission created: {permission_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom permission: {e}")
            return False
    
    def list_permissions(self) -> List[str]:
        """Lista todas as permissões disponíveis."""
        return list(self.system_permissions.keys())
    
    def list_permissions_by_resource(self, resource: str) -> List[str]:
        """Lista permissões por recurso."""
        return [
            perm for perm in self.system_permissions.keys()
            if perm.startswith(f"{resource}:")
        ]
    
    def validate_permission_string(self, permission: str) -> bool:
        """Valida formato da string de permissão."""
        try:
            Permission.from_string(permission)
            return True
        except ValueError:
            return False


# Decoradores para verificação de permissões
def require_permission(permission: str):
    """Decorador para exigir permissão específica."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Esta é uma implementação simplificada
            # Em produção, extrair usuário do contexto da request
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """Decorador para exigir role específico."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Esta é uma implementação simplificada
            # Em produção, extrair usuário do contexto da request
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Instância global
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Obtém instância singleton do PermissionManager."""
    global _permission_manager
    
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    
    return _permission_manager
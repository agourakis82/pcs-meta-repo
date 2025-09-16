"""
Sistema H3 - Handler JWT

Gerenciamento de tokens JWT para autenticação.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handler para tokens JWT."""

    def __init__(
        self,
        secret_key: str = "your-secret-key",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    async def create_access_token(self, data: Dict[str, Any]) -> str:
        """Cria access token JWT."""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

            to_encode.update(
                {"exp": expire, "iat": datetime.utcnow(), "type": "access"}
            )

            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=self.algorithm
            )
            return encoded_jwt

        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise

    async def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Cria refresh token JWT."""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

            to_encode.update(
                {"exp": expire, "iat": datetime.utcnow(), "type": "refresh"}
            )

            encoded_jwt = jwt.encode(
                to_encode, self.secret_key, algorithm=self.algorithm
            )
            return encoded_jwt

        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica e decodifica access token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verificar tipo do token
            if payload.get("type") != "access":
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    async def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifica e decodifica refresh token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verificar tipo do token
            if payload.get("type") != "refresh":
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid refresh token")
            return None
        except Exception as e:
            logger.error(f"Error verifying refresh token: {e}")
            return None

    async def decode_token_without_verification(
        self, token: str
    ) -> Optional[Dict[str, Any]]:
        """Decodifica token sem verificar assinatura (para debug)."""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return None

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Obtém data de expiração do token."""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.utcfromtimestamp(exp_timestamp)
            return None
        except Exception:
            return None

    def is_token_expired(self, token: str) -> bool:
        """Verifica se token está expirado."""
        expiry = self.get_token_expiry(token)
        if expiry:
            return datetime.utcnow() > expiry
        return True

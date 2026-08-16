"""
Service-to-Service Authentication for ERP03 Integration.

This module provides JWT validation and API key management for secure
communication between AI-BACKEND and ERP-BACKEND.
"""

import jwt
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Types of authentication tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    SERVICE = "service"


@dataclass
class TokenPayload:
    """JWT token payload structure."""
    sub: str  # Subject (user_id or service_id)
    iss: str  # Issuer
    aud: str  # Audience
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    jti: str  # JWT ID (unique identifier)
    type: TokenType  # Token type
    scopes: List[str]  # Permission scopes
    metadata: Dict[str, Any]  # Additional metadata


class JWTValidator:
    """
    JWT token validator for service-to-service authentication.
    
    Supports:
    - Token validation and decoding
    - Token expiration checking
    - Scope/permission verification
    - Token refresh
    """
    
    def __init__(
        self,
        secret_key: str,
        issuer: str = "erp-backend",
        audience: str = "ai-backend",
        algorithm: str = "HS256"
    ):
        self.secret_key = secret_key.encode('utf-8')
        self.issuer = issuer
        self.audience = audience
        self.algorithm = algorithm
    
    def create_token(
        self,
        subject: str,
        token_type: TokenType = TokenType.ACCESS,
        expires_in: timedelta = timedelta(hours=1),
        scopes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a signed JWT token.
        
        Args:
            subject: Token subject (user_id or service_id)
            token_type: Type of token (access/refresh/service)
            expires_in: Token validity duration
            scopes: List of permission scopes
            metadata: Additional metadata to include
            
        Returns:
            Signed JWT token string
        """
        now = datetime.utcnow()
        
        payload = {
            "sub": subject,
            "iss": self.issuer,
            "aud": self.audience,
            "exp": now + expires_in,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "type": token_type.value,
            "scopes": scopes or [],
            "metadata": metadata or {}
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Created {token_type.value} token for subject {subject}")
        return token
    
    def validate_token(self, token: str) -> TokenPayload:
        """
        Validate and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token has expired
            jwt.InvalidIssuerError: If issuer is invalid
            jwt.InvalidAudienceError: If audience is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True
                },
                issuer=self.issuer,
                audience=self.audience
            )
            
            token_payload = TokenPayload(
                sub=payload["sub"],
                iss=payload["iss"],
                aud=payload["aud"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload["jti"],
                type=TokenType(payload["type"]),
                scopes=payload.get("scopes", []),
                metadata=payload.get("metadata", {})
            )
            
            logger.debug(f"Validated token for subject {payload['sub']}")
            return token_payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except jwt.InvalidIssuerError:
            logger.warning("Invalid token issuer")
            raise
        except jwt.InvalidAudienceError:
            logger.warning("Invalid token audience")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise
    
    def refresh_token(self, refresh_token: str) -> str:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            jwt.InvalidTokenError: If refresh token is invalid
            ValueError: If token is not a refresh token
        """
        payload = self.validate_token(refresh_token)
        
        if payload.type != TokenType.REFRESH:
            raise ValueError("Token is not a refresh token")
        
        # Create new access token with same subject and scopes
        return self.create_token(
            subject=payload.sub,
            token_type=TokenType.ACCESS,
            expires_in=timedelta(hours=1),
            scopes=payload.scopes,
            metadata=payload.metadata
        )
    
    def verify_scope(self, token: str, required_scope: str) -> bool:
        """
        Verify that a token has a specific scope.
        
        Args:
            token: JWT token string
            required_scope: Required permission scope
            
        Returns:
            True if token has the required scope
        """
        try:
            payload = self.validate_token(token)
            return required_scope in payload.scopes
        except jwt.InvalidTokenError:
            return False
    
    def verify_scopes(self, token: str, required_scopes: List[str]) -> bool:
        """
        Verify that a token has all required scopes.
        
        Args:
            token: JWT token string
            required_scopes: List of required permission scopes
            
        Returns:
            True if token has all required scopes
        """
        try:
            payload = self.validate_token(token)
            return all(scope in payload.scopes for scope in required_scopes)
        except jwt.InvalidTokenError:
            return False


class APIKeyManager:
    """
    API key management for service-to-service authentication.
    
    Features:
    - API key generation
    - API key hashing and validation
    - API key rotation
    - Key metadata storage
    """
    
    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}  # In-memory storage (use DB in production)
    
    def generate_key(
        self,
        name: str,
        service_id: str,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a new API key.
        
        Args:
            name: Human-readable name for the key
            service_id: Service identifier
            scopes: Allowed permission scopes
            expires_at: Optional expiration time
            metadata: Additional metadata
            
        Returns:
            Generated API key (store this securely, it won't be shown again)
        """
        # Generate random key
        raw_key = secrets.token_urlsafe(32)
        
        # Hash the key for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Store key metadata
        self._keys[key_hash] = {
            "name": name,
            "service_id": service_id,
            "scopes": scopes or [],
            "expires_at": expires_at,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "last_used_at": None,
            "is_active": True
        }
        
        logger.info(f"Generated API key '{name}' for service {service_id}")
        return raw_key
    
    def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return its metadata.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Key metadata if valid, None otherwise
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        key_data = self._keys.get(key_hash)
        if not key_data:
            logger.warning("API key not found")
            return None
        
        if not key_data["is_active"]:
            logger.warning(f"API key '{key_data['name']}' is deactivated")
            return None
        
        if key_data["expires_at"] and datetime.utcnow() > key_data["expires_at"]:
            logger.warning(f"API key '{key_data['name']}' has expired")
            return None
        
        # Update last used timestamp
        key_data["last_used_at"] = datetime.utcnow()
        
        return {
            "service_id": key_data["service_id"],
            "scopes": key_data["scopes"],
            "metadata": key_data["metadata"]
        }
    
    def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key: API key to revoke
            
        Returns:
            True if key was revoked, False if not found
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self._keys:
            self._keys[key_hash]["is_active"] = False
            logger.info(f"Revoked API key '{self._keys[key_hash]['name']}'")
            return True
        
        return False
    
    def rotate_key(
        self,
        old_api_key: str,
        new_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Rotate an API key (revoke old, create new).
        
        Args:
            old_api_key: Current API key
            new_name: Optional new name for the key
            
        Returns:
            New API key if rotation successful, None otherwise
        """
        # Validate old key
        key_data = self.validate_key(old_api_key)
        if not key_data:
            return None
        
        key_hash = hashlib.sha256(old_api_key.encode()).hexdigest()
        old_key_data = self._keys[key_hash]
        
        # Revoke old key
        self.revoke_key(old_api_key)
        
        # Generate new key with same properties
        return self.generate_key(
            name=new_name or f"{old_key_data['name']} (rotated)",
            service_id=old_key_data["service_id"],
            scopes=old_key_data["scopes"],
            expires_at=old_key_data["expires_at"],
            metadata=old_key_data["metadata"]
        )
    
    def list_keys(self, service_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all API keys, optionally filtered by service.
        
        Args:
            service_id: Optional service ID filter
            
        Returns:
            List of key metadata (without hashes)
        """
        keys = []
        for key_hash, key_data in self._keys.items():
            if service_id and key_data["service_id"] != service_id:
                continue
            
            keys.append({
                "name": key_data["name"],
                "service_id": key_data["service_id"],
                "scopes": key_data["scopes"],
                "expires_at": key_data["expires_at"],
                "created_at": key_data["created_at"],
                "last_used_at": key_data["last_used_at"],
                "is_active": key_data["is_active"]
            })
        
        return keys


# ============================================================================
# Authentication middleware helper
# ============================================================================

def extract_token_from_header(headers: Dict[str, str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        Token string if found, None otherwise
    """
    auth_header = headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None


def extract_api_key_from_header(headers: Dict[str, str]) -> Optional[str]:
    """
    Extract API key from X-API-Key header.
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        API key if found, None otherwise
    """
    return headers.get("X-API-Key")

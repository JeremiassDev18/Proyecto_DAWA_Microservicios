import datetime
import functools
import jwt
import uuid
from typing import Any, Callable, Dict, List, Optional

from argon2 import PasswordHasher
from flask import jsonify, request, g

from config import Config

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except Exception:
        return False


def create_access_token(
    subject: Dict[str, Any],
    expires_delta: Optional[int] = None,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
) -> str:
    now = datetime.datetime.utcnow()
    expires_in = expires_delta or Config.JWT_ACCESS_TOKEN_EXPIRES
    jti = str(uuid.uuid4())  # JWT ID for token revocation
    
    payload = {
        "sub": str(subject.get("id", "unknown")),
        "iat": now,
        "exp": now + datetime.timedelta(seconds=expires_in),
        "type": "access",
        "jti": jti,
        "roles": roles or [],
        "permissions": permissions or [],
        "user": subject,
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Dict:
    return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])


def authorize(required_roles: Optional[List[str]] = None, required_permissions: Optional[List[str]] = None) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Token no proporcionado"}), 401

            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except Exception:
                return jsonify({"error": "Token inválido o expirado"}), 401

            # Check if token is blacklisted
            from db import execute_query
            jti = payload.get("jti")
            if jti:
                blacklist_entry = execute_query(
                    "SELECT id FROM token_blacklist WHERE token_jti = %s LIMIT 1",
                    (jti,),
                    fetch_one=True
                )
                if blacklist_entry:
                    return jsonify({"error": "Token revocado"}), 401

            user_roles = payload.get("roles", [])
            user_permissions = payload.get("permissions", [])

            if required_roles:
                if not any(role in user_roles for role in required_roles):
                    return jsonify({"error": "No autorizado"}), 403

            if required_permissions:
                if not any(permission in user_permissions for permission in required_permissions):
                    return jsonify({"error": "No autorizado"}), 403

            # Store user info in flask's g object for access in route handler
            g.user_id = payload.get("user", {}).get("id")
            g.roles = user_roles
            g.permissions = user_permissions
            g.jti = jti
            request.user = payload
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def blacklist_token(jti: str, usuario_id: Optional[int] = None, reason: str = "logout", expires_at: Optional[datetime.datetime] = None) -> bool:
    """Add a token to the blacklist."""
    from db import execute_query
    
    if not expires_at:
        # Default to 24 hours
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    
    query = (
        "INSERT INTO token_blacklist (token_jti, usuario_id, expira_en, razon) "
        "VALUES (%s, %s, %s, %s)"
    )
    
    try:
        execute_query(query, (jti, usuario_id, expires_at, reason))
        return True
    except Exception:
        return False


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token is blacklisted."""
    from db import execute_query
    
    if not jti:
        return False
    
    result = execute_query(
        "SELECT id FROM token_blacklist WHERE token_jti = %s AND expira_en > NOW() LIMIT 1",
        (jti,),
        fetch_one=True
    )
    return result is not None

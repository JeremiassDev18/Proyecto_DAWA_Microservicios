import jwt
import os
from functools import wraps
from flask import jsonify, request

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "1a6790ea7aee933b903e74fcaa2804dfbf61387d6c4d7cb61206fd32b211958b")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

PUBLIC_PATHS = {"/api/tutorias/health"}


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        path = request.path.rstrip("/")
        if path in PUBLIC_PATHS:
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token no proporcionado"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except Exception:
            return jsonify({"error": "Token inválido"}), 401

        request.user = payload
        return f(*args, **kwargs)
    return decorated


def authorize(*, roles: list = None, permissions: list = None):
    def decorator(f):
        @wraps(f)
        @jwt_required
        def wrapper(*args, **kwargs):
            payload = request.user
            user_roles = payload.get("roles", [])
            user_permissions = payload.get("permissions", [])

            if roles and not any(r in user_roles for r in roles):
                return jsonify({"error": "Acceso denegado. Rol requerido"}), 403
            if permissions and not any(p in user_permissions for p in permissions):
                return jsonify({"error": "Acceso denegado. Permiso requerido"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

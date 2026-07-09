import jwt
import os
from functools import wraps
from flask import request, jsonify

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "1a6790ea7aee933b903e74fcaa2804dfbf61387d6c4d7cb61206fd32b211958b")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def requiere_roles(roles_permitidos):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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

            user_roles = payload.get("roles", [])
            tiene_permiso = any(
                rol.lower() in [r.lower() for r in user_roles]
                for rol in roles_permitidos
            )
            if not tiene_permiso:
                return jsonify({"error": "Acceso denegado. No tiene permisos para esta acción"}), 403

            request.user = payload
            return func(*args, **kwargs)
        return wrapper
    return decorador

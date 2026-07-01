from functools import wraps
from flask import request, jsonify


def requiere_roles(roles_permitidos):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = request.headers.get("X-User-Id")
            roles = request.headers.get("X-Roles", "")

            if not user_id or not roles:
                return jsonify({
                    "error": "No autorizado. Faltan headers de autenticación"
                }), 401

            roles_usuario = [rol.strip().lower() for rol in roles.split(",")]

            tiene_permiso = any(
                rol.lower() in roles_usuario for rol in roles_permitidos
            )

            if not tiene_permiso:
                return jsonify({
                    "error": "Acceso denegado. No tiene permisos para esta acción"
                }), 403

            return func(*args, **kwargs)

        return wrapper
    return decorador
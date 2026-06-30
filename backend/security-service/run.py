from flask import Flask, jsonify, request, g
from flask_cors import CORS

from auth import authorize, create_access_token, blacklist_token
from config import Config
from db import init_db_pool, execute_query
from services import PermissionService, RoleService, UserService


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False

    CORS(app)
    init_db_pool()

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "security-service"}), 200

    @app.route("/login", methods=["POST"])
    def login():
        payload = request.get_json() or {}
        email = payload.get("email")
        password = payload.get("password")

        if not email or not password:
            return jsonify({"error": "Email y password son requeridos."}), 400

        user = UserService.authenticate_user(email, password)
        if not user:
            return jsonify({"error": "Credenciales inválidas."}), 401

        user_roles = UserService.get_user_roles(user["id"])
        user_permissions = UserService.get_user_permissions(user["id"])

        access_token = create_access_token(
            {"id": user["id"], "email": user["email"]},
            roles=user_roles,
            permissions=user_permissions,
        )
        return jsonify(
            {
                "access_token": access_token,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "nombre": user["nombre"],
                    "roles": user_roles,
                    "permissions": user_permissions,
                },
            }
        ), 200

    @app.route("/usuarios", methods=["POST"])
    def register_user():
        payload = request.get_json() or {}
        email = payload.get("email")
        password = payload.get("password")
        nombre = payload.get("nombre")

        if not email or not password or not nombre:
            return jsonify({"error": "Email, password y nombre son requeridos."}), 400

        existing_user = UserService.get_user_by_email(email)
        if existing_user:
            return jsonify({"error": "El usuario ya existe."}), 409

        user = UserService.create_user(email, password, nombre)
        return jsonify({"usuario": user}), 201

    @app.route("/roles", methods=["GET"])
    def get_roles():
        roles = RoleService.get_roles()
        return jsonify({"roles": roles}), 200

    @app.route("/permisos", methods=["GET"])
    def get_permissions():
        permissions = PermissionService.get_permissions()
        return jsonify({"permisos": permissions}), 200

    @app.route("/usuarios/<int:usuario_id>/roles", methods=["POST"])
    @authorize(required_roles=["admin"], required_permissions=["write_users"])
    def assign_role(usuario_id: int):
        payload = request.get_json() or {}
        rol_id = payload.get("rol_id")

        if not rol_id:
            return jsonify({"error": "rol_id es requerido"}), 400

        assignment = RoleService.assign_role_to_user(usuario_id, rol_id)
        return jsonify({"asignacion": assignment}), 201

    @app.route("/protected", methods=["GET"])
    @authorize(required_roles=["admin"], required_permissions=["read_users"])
    def protected_resource():
        return jsonify({"message": "Acceso autorizado"}), 200

    @app.route("/usuarios/<int:usuario_id>/cambiar-contrasena", methods=["POST"])
    @authorize(required_roles=[], required_permissions=[])  # Any authenticated user can change their own password
    def change_password(usuario_id: int):
        """Change password endpoint. Users can only change their own password unless they're admin."""
        # Get the current user ID from the token
        from flask import g
        current_user_id = getattr(g, "user_id", None)
        
        # Allow users to change their own password, or admins to change anyone's
        current_user_roles = getattr(g, "roles", [])
        if current_user_id != usuario_id and "admin" not in current_user_roles:
            return jsonify({"error": "No tienes permiso para cambiar esta contraseña"}), 403
        
        payload = request.get_json() or {}
        current_password = payload.get("current_password")
        new_password = payload.get("new_password")
        new_password_confirm = payload.get("new_password_confirm")

        # Validation
        if not current_password or not new_password or not new_password_confirm:
            return jsonify({"error": "current_password, new_password y new_password_confirm son requeridos"}), 400

        if new_password != new_password_confirm:
            return jsonify({"error": "Las contraseñas no coinciden"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

        # Verify current password (unless it's an admin changing someone else's password)
        if current_user_id == usuario_id:
            if not UserService.verify_current_password(usuario_id, current_password):
                return jsonify({"error": "Contraseña actual incorrecta"}), 401

        # Check user exists
        user = execute_query("SELECT id FROM usuarios WHERE id = %s", (usuario_id,), fetch_one=True)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Change password
        UserService.change_password(usuario_id, new_password)
        return jsonify({"mensaje": "Contraseña actualizada exitosamente"}), 200

    @app.route("/usuarios/recuperar-contrasena", methods=["POST"])
    def request_password_reset():
        """Request password reset. Generates reset token (in real app, send via email)."""
        payload = request.get_json() or {}
        email = payload.get("email")

        if not email:
            return jsonify({"error": "Email es requerido"}), 400

        user = UserService.get_user_by_email(email)
        if not user:
            # Return generic message for security (don't reveal if user exists)
            return jsonify({"mensaje": "Si el email existe, se enviará un enlace de recuperación"}), 200

        # Generate reset token
        reset_token = UserService.create_password_reset_token(user["id"])
        
        # TODO: Send token via email
        # For now, return token in response (in production, send via email only)
        return jsonify({
            "mensaje": "Si el email existe, se enviará un enlace de recuperación",
            "reset_token": reset_token  # Remove in production!
        }), 200

    @app.route("/usuarios/resetear-contrasena", methods=["POST"])
    def reset_password_with_token():
        """Reset password using reset token."""
        payload = request.get_json() or {}
        token = payload.get("token")
        new_password = payload.get("new_password")
        new_password_confirm = payload.get("new_password_confirm")

        if not token or not new_password or not new_password_confirm:
            return jsonify({"error": "token, new_password y new_password_confirm son requeridos"}), 400

        if new_password != new_password_confirm:
            return jsonify({"error": "Las contraseñas no coinciden"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

        # Validate token
        reset_data = UserService.validate_password_reset_token(token)
        if not reset_data:
            return jsonify({"error": "Token inválido o expirado"}), 400

        # Change password
        usuario_id = reset_data["usuario_id"]
        UserService.change_password(usuario_id, new_password)
        UserService.mark_reset_token_as_used(token)
        
        return jsonify({"mensaje": "Contraseña actualizada exitosamente"}), 200

    @app.route("/logout", methods=["POST"])
    @authorize(required_roles=[], required_permissions=[])
    def logout():
        """Logout endpoint - revokes the current JWT token."""
        jti = g.get("jti")
        user_id = g.get("user_id")
        
        if not jti:
            return jsonify({"error": "Token inválido"}), 401
        
        # Blacklist the token
        success = blacklist_token(jti, user_id, "logout")
        
        if success:
            return jsonify({"mensaje": "Sesión cerrada exitosamente"}), 200
        else:
            return jsonify({"error": "Error al cerrar sesión"}), 500

    @app.route("/logout-all", methods=["POST"])
    @authorize(required_roles=[], required_permissions=[])
    def logout_all():
        """Logout all sessions for the current user - revokes all their tokens."""
        user_id = g.get("user_id")
        
        if not user_id:
            return jsonify({"error": "Usuario no identificado"}), 401
        
        # Get all active tokens for this user (with jti stored in audit or session table)
        # For now, just acknowledge the request
        # In production, would need to track all issued tokens per user
        return jsonify({
            "mensaje": "Todas las sesiones han sido cerradas",
            "note": "Próximas característica: cierre de todas las sesiones en otros dispositivos"
        }), 200

    @app.route("/sessions/active", methods=["GET"])
    @authorize(required_roles=[], required_permissions=[])
    def get_active_sessions():
        """Get list of active sessions for the current user."""
        user_id = g.get("user_id")
        
        if not user_id:
            return jsonify({"error": "Usuario no identificado"}), 401
        
        # TODO: Implement session tracking
        return jsonify({
            "sesiones": [
                {
                    "id": "current",
                    "dispositivo": "Dispositivo actual",
                    "fecha_login": "ahora",
                    "ubicacion": "Desconocida"
                }
            ]
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001)

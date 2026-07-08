from flask import Flask, jsonify, request, g
from flask_cors import CORS

from auth import authorize, create_access_token, create_refresh_token, validate_refresh_token, revoke_refresh_token, blacklist_token, decode_token, is_token_blacklisted
import json
import datetime
from app.utils.audit import audit_log
from app.utils.email_utils import send_password_reset_email
from app.routes.permission_routes import permission_bp
from config import Config
from db import init_db_pool, execute_query
from services import RoleService, UserService
from services import SessionService


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JSON_SORT_KEYS"] = False

    CORS(app)
    init_db_pool()
    app.register_blueprint(permission_bp)

    @app.before_request
    def check_blacklisted_token():
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except Exception:
            # invalid token will be handled by authorize decorator where needed
            return None

        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return jsonify({"error": "Token revocado"}), 401

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "security-service"}), 200

    @app.route("/login", methods=["POST"])
    @audit_log("login")
    def login():
        payload = request.get_json() or {}
        email = payload.get("email")
        password = payload.get("password")

        if not email or not password:
            return jsonify({"error": "Email y password son requeridos."}), 400

        try:
            user = UserService.authenticate_user(email, password)
        except Exception as exc:
            return jsonify({"error": "No se pudo validar las credenciales", "detail": str(exc)}), 500

        if not user:
            # Log failed login attempt
            try:
                remote_addr = request.remote_addr or request.headers.get("X-Forwarded-For", None)
                details = {"email": email, "reason": "invalid_credentials"}
                execute_query(
                    "INSERT INTO auditoria (usuario_id, accion, direccion_ip, detalles) VALUES (%s, %s, %s, %s::jsonb)",
                    (None, "login_failed", remote_addr, json.dumps(details)),
                )
            except Exception:
                pass
            return jsonify({"error": "Credenciales inválidas."}), 401

        g.audit_user_id = user["id"]
        user_roles = UserService.get_user_roles(user["id"])
        user_permissions = UserService.get_user_permissions(user["id"])

        access_token, jti, exp = create_access_token(
            {"id": user["id"], "email": user["email"]},
            roles=user_roles,
            permissions=user_permissions,
            return_jti=True,
        )

        try:
            session = execute_query(
                "SELECT id FROM sessions WHERE token_jti = %s LIMIT 1",
                (jti,),
                fetch_one=True,
            )
            if session:
                refresh_token = create_refresh_token(session["id"], user["id"])
            else:
                refresh_token = None
        except Exception:
            refresh_token = None

        response = {
            "access_token": access_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "nombre": user["nombre"],
                "roles": user_roles,
                "permissions": user_permissions,
            },
        }

        if refresh_token:
            response["refresh_token"] = refresh_token

        return jsonify(response), 200

    @app.route("/refresh", methods=["POST"])
    def refresh_access_token():
        payload = request.get_json() or {}
        refresh_token = payload.get("refresh_token")
        usuario_id = payload.get("usuario_id")

        if not refresh_token or not usuario_id:
            return jsonify({"error": "refresh_token y usuario_id son requeridos"}), 400

        refresh_data = validate_refresh_token(refresh_token, usuario_id)
        if not refresh_data:
            return jsonify({"error": "Refresh token inválido o expirado"}), 401

        session_id = refresh_data["session_id"]
        user = UserService.get_user_by_id(usuario_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        user_roles = UserService.get_user_roles(usuario_id)
        user_permissions = UserService.get_user_permissions(usuario_id)

        access_token, jti, exp = create_access_token(
            {"id": user["id"], "email": user["email"]},
            roles=user_roles,
            permissions=user_permissions,
            return_jti=True,
        )

        try:
            execute_query(
                "UPDATE sessions SET token_jti = %s, expira_en = %s, revocado = FALSE, revocado_en = NULL WHERE id = %s",
                (jti, exp, session_id),
            )
        except Exception:
            pass

        return jsonify({"access_token": access_token}), 200

    @app.route("/refresh/revoke", methods=["POST"])
    def revoke_refresh():
        payload = request.get_json() or {}
        refresh_token = payload.get("refresh_token")
        if not refresh_token:
            return jsonify({"error": "refresh_token es requerido"}), 400

        success = revoke_refresh_token(refresh_token, reason="manual_revoke")
        if not success:
            return jsonify({"error": "No se pudo revocar el refresh token"}), 400
        return jsonify({"mensaje": "Refresh token revocado"}), 200

    @app.route("/usuarios", methods=["POST"])
    def register_user():
        payload = request.get_json() or {}
        email = payload.get("email")
        password = payload.get("password")
        nombre = payload.get("nombre")

        if not email or not password or not nombre:
            return jsonify({"error": "Email, password y nombre son requeridos."}), 400

        try:
            existing_user = UserService.get_user_by_email(email)
            if existing_user:
                return jsonify({"error": "El usuario ya existe."}), 409

            user = UserService.create_user(email, password, nombre)
        except Exception as exc:
            return jsonify({"error": "No se pudo completar la operación de registro", "detail": str(exc)}), 500

        return jsonify({"usuario": user}), 201

    @app.route("/usuarios", methods=["GET"])
    @authorize(required_roles=["admin"], required_permissions=["read_users"])
    def list_users():
        usuarios = UserService.get_users()
        return jsonify({"usuarios": usuarios}), 200

    @app.route("/usuarios/<int:usuario_id>", methods=["GET"])
    @authorize(required_roles=["admin"], required_permissions=["read_users"])
    def get_user(usuario_id: int):
        user = UserService.get_user_by_id(usuario_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify({"usuario": user}), 200

    @app.route("/usuarios/me", methods=["GET"])
    def get_current_user():
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except Exception as exc:
            return jsonify({"error": "Token inválido", "detail": str(exc)}), 401
        usuario_id = payload.get("id") or payload.get("sub")
        if not usuario_id:
            return jsonify({"error": "Token no contiene usuario"}), 401
        user = UserService.get_user_by_id(usuario_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        user_roles = UserService.get_user_roles(usuario_id)
        user_permissions = UserService.get_user_permissions(usuario_id)
        user["roles"] = user_roles
        user["permissions"] = user_permissions
        return jsonify(user), 200

    @app.route("/usuarios/<int:usuario_id>", methods=["PUT"])
    @audit_log("update_user")
    @authorize(required_roles=["admin"], required_permissions=["write_users"])
    def update_user(usuario_id: int):
        payload = request.get_json() or {}
        nombre = payload.get("nombre")
        estado = payload.get("estado", True)

        if nombre is None:
            return jsonify({"error": "nombre es requerido"}), 400

        updated = UserService.update_user(usuario_id, nombre, bool(estado))
        if not updated:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify({"usuario": updated}), 200

    @app.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
    @audit_log("delete_user")
    @authorize(required_roles=["admin"], required_permissions=["write_users"])
    def delete_user(usuario_id: int):
        deleted = UserService.delete_user(usuario_id)
        if not deleted:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify({"mensaje": "Usuario eliminado exitosamente"}), 200

    @app.route("/roles", methods=["GET"])
    def get_roles():
        roles = RoleService.get_roles()
        return jsonify({"roles": roles}), 200

    @app.route("/roles", methods=["POST"])
    @audit_log("create_role")
    @authorize(required_roles=["admin"], required_permissions=["write_users"])
    def create_role():
        payload = request.get_json() or {}
        nombre_rol = payload.get("nombre_rol")
        descripcion = payload.get("descripcion")

        if not nombre_rol:
            return jsonify({"error": "nombre_rol es requerido"}), 400

        role = RoleService.create_role(nombre_rol, descripcion)
        return jsonify({"rol": role}), 201

    @app.route("/roles/<int:rol_id>", methods=["PUT"])
    @audit_log("update_role")
    @authorize(required_roles=["admin"], required_permissions=["write_users"])
    def update_role(rol_id: int):
        payload = request.get_json() or {}
        nombre_rol = payload.get("nombre_rol")
        descripcion = payload.get("descripcion")

        if not nombre_rol:
            return jsonify({"error": "nombre_rol es requerido"}), 400

        updated = RoleService.update_role(rol_id, nombre_rol, descripcion)
        if not updated:
            return jsonify({"error": "Rol no encontrado"}), 404

        return jsonify({"rol": updated}), 200

    @app.route("/roles/<int:rol_id>", methods=["DELETE"])
    @audit_log("delete_role")
    @authorize(required_roles=["admin"], required_permissions=["write_users"])
    def delete_role(rol_id: int):
        deleted = RoleService.delete_role(rol_id)
        if not deleted:
            return jsonify({"error": "Rol no encontrado"}), 404
        return jsonify({"mensaje": "Rol eliminado exitosamente"}), 200

    @app.route("/usuarios/<int:usuario_id>/roles", methods=["POST"])
    @audit_log("assign_role")
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
    @audit_log("change_password")
    @authorize(required_roles=[], required_permissions=[])  # cualquier usuario puede cambiar su propia contraseña, admin puede cambiar la de otros
    def change_password(usuario_id: int):
        """Change password endpoint. Users can only change their own password unless they're admin."""
        # obtener el usuario actual desde g
        from flask import g
        current_user_id = getattr(g, "user_id", None)
        
        # revisar si el usuario actual es admin o si está cambiando su propia contraseña
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

        # verificar la contraseña actual solo si el usuario está cambiando su propia contraseña
        if current_user_id == usuario_id:
            if not UserService.verify_current_password(usuario_id, current_password):
                return jsonify({"error": "Contraseña actual incorrecta"}), 401

        # revisar si el usuario existe antes de cambiar la contraseña
        user = execute_query("SELECT id FROM usuarios WHERE id = %s", (usuario_id,), fetch_one=True)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # cambiar la contraseña y registrar en la auditoria
        # registrar el usuario cuyo password se está cambiando, no el que hace la acción (que puede ser admin)
        g.audit_details = {"target_user_id": usuario_id}
        UserService.change_password(usuario_id, new_password)
        return jsonify({"mensaje": "Contraseña actualizada exitosamente"}), 200




    @app.route("/usuarios/recuperar-contrasena", methods=["POST"])
    def request_password_reset():
        """Request password reset. Generates reset token (in real app, send via email)."""
        payload = request.get_json() or {}
        email = payload.get("email")

        if not email:
            return jsonify({"error": "Email es requerido"}), 400

        try:
            user = UserService.get_user_by_email(email)
        except Exception as exc:
            return jsonify({"error": "No se pudo procesar la solicitud de recuperación", "detail": str(exc)}), 500

        if not user:
            return jsonify({"mensaje": "Si el email existe, se enviará un enlace de recuperación"}), 200

        try:
            reset_token = UserService.create_password_reset_token(user["id"])
            send_password_reset_email(user["email"], reset_token)
        except Exception as exc:
            return jsonify({"error": "No se pudo enviar el correo de recuperación", "detail": str(exc)}), 500

        return jsonify({"mensaje": "Si el email existe, se enviará un enlace de recuperación"}), 200



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

        # Validar token
        reset_data = UserService.validate_password_reset_token(token)
        if not reset_data:
            return jsonify({"error": "Token inválido o expirado"}), 400

        # Cambiar la contraseña del usuario y marcar el token como usado
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
        # Revoke all sessions for the user using SessionService
        revoked_count = SessionService.revoke_all_sessions(user_id, reason="logout_all")

        return jsonify({
            "mensaje": "Todas las sesiones han sido cerradas",
            "revoked": revoked_count
        }), 200




    @app.route("/sessions/active", methods=["GET"])
    @authorize(required_roles=[], required_permissions=[])
    def get_active_sessions():
        """Get list of active sessions for the current user."""
        user_id = g.get("user_id")
        
        if not user_id:
            return jsonify({"error": "Usuario no identificado"}), 401
        
        sessions = SessionService.get_active_sessions(user_id)

        for s in (sessions or []):
            f = s.get("creado_en")
            if hasattr(f, "isoformat"):
                s["creado_en"] = f.isoformat()
            e = s.get("expira_en")
            if hasattr(e, "isoformat"):
                s["expira_en"] = e.isoformat()

        return jsonify({"sesiones": sessions or []}), 200

    @app.route("/auditoria", methods=["GET"])
    @authorize(required_roles=["admin"], required_permissions=["read_reports"])
    def list_auditoria():
        """List audit records with optional filters: usuario_id, accion, desde, hasta, limit, offset"""
        usuario_id = request.args.get("usuario_id")
        accion = request.args.get("accion")
        desde = request.args.get("desde")
        hasta = request.args.get("hasta")
        try:
            limit = int(request.args.get("limit", 100))
        except Exception:
            limit = 100
        try:
            offset = int(request.args.get("offset", 0))
        except Exception:
            offset = 0

        where_clauses = []
        params = []
        if usuario_id:
            where_clauses.append("usuario_id = %s")
            params.append(usuario_id)
        if accion:
            where_clauses.append("accion = %s")
            params.append(accion)
        if desde:
            where_clauses.append("fecha >= %s")
            params.append(desde)
        if hasta:
            where_clauses.append("fecha <= %s")
            params.append(hasta)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        query = (
            "SELECT id, usuario_id, accion, fecha, direccion_ip, detalles "
            f"FROM auditoria {where_sql} ORDER BY fecha DESC LIMIT %s OFFSET %s"
        )
        params.extend([limit, offset])

        results = execute_query(query, tuple(params), fetch_all=True)
        for row in (results or []):
            f = row.get("fecha")
            if isinstance(f, datetime.datetime):
                row["fecha"] = f.isoformat()

        return jsonify({"auditoria": results}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001)

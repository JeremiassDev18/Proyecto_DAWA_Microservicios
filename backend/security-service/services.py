from typing import Any, Dict, List, Optional
import secrets
import datetime

from db import execute_query
from auth import hash_password, verify_password


class UserService:
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM usuarios WHERE email = %s LIMIT 1"
        return execute_query(query, (email,), fetch_one=True)

    @staticmethod
    def create_user(email: str, password: str, nombre: str) -> Dict[str, Any]:
        password_hash = hash_password(password)
        query = (
            "INSERT INTO usuarios (email, password_hash, nombre, estado) "
            "VALUES (%s, %s, %s, TRUE) RETURNING id, email, nombre, estado, creado_en"
        )
        return execute_query(query, (email, password_hash, nombre), fetch_one=True)

    @staticmethod
    def get_users() -> List[Dict[str, Any]]:
        query = "SELECT id, email, nombre, estado, creado_en FROM usuarios"
        return execute_query(query, fetch_all=True)

    @staticmethod
    def get_user_by_id(usuario_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT id, email, nombre, estado, creado_en FROM usuarios WHERE id = %s LIMIT 1"
        return execute_query(query, (usuario_id,), fetch_one=True)

    @staticmethod
    def update_user(usuario_id: int, nombre: str, estado: bool) -> Optional[Dict[str, Any]]:
        query = (
            "UPDATE usuarios SET nombre = %s, estado = %s WHERE id = %s "
            "RETURNING id, email, nombre, estado, creado_en"
        )
        return execute_query(query, (nombre, estado, usuario_id), fetch_one=True)

    @staticmethod
    def delete_user(usuario_id: int) -> bool:
        query = "DELETE FROM usuarios WHERE id = %s RETURNING id"
        result = execute_query(query, (usuario_id,), fetch_one=True)
        return result is not None

    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        user = UserService.get_user_by_email(email)
        if not user:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        return user

    @staticmethod
    def get_user_roles(usuario_id: int) -> List[str]:
        query = """
            SELECT r.nombre_rol FROM roles r
            JOIN usuarios_roles ur ON r.id = ur.rol_id
            WHERE ur.usuario_id = %s
        """
        result = execute_query(query, (usuario_id,), fetch_all=True)
        return [row["nombre_rol"] for row in result] if result else []

    @staticmethod
    def get_user_permissions(usuario_id: int) -> List[str]:
        query = """
            SELECT DISTINCT p.nombre_permiso FROM permisos p
            JOIN roles_permisos rp ON p.id = rp.permiso_id
            JOIN usuarios_roles ur ON rp.rol_id = ur.rol_id
            WHERE ur.usuario_id = %s
        """
        result = execute_query(query, (usuario_id,), fetch_all=True)
        return [row["nombre_permiso"] for row in result] if result else []

    @staticmethod
    def change_password(usuario_id: int, new_password: str) -> bool:
        """Change a user's password."""
        new_password_hash = hash_password(new_password)
        query = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
        execute_query(query, (new_password_hash, usuario_id))
        return True

    @staticmethod
    def verify_current_password(usuario_id: int, current_password: str) -> bool:
        """Verify a user's current password before allowing change."""
        query = "SELECT password_hash FROM usuarios WHERE id = %s LIMIT 1"
        result = execute_query(query, (usuario_id,), fetch_one=True)
        
        if not result:
            return False
        
        return verify_password(current_password, result["password_hash"])

    @staticmethod
    def create_password_reset_token(usuario_id: int, expires_in_hours: int = 24) -> str:
        """Generate a password reset token for a user."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)
        
        query = (
            "INSERT INTO password_reset_tokens (usuario_id, token, expira_en) "
            "VALUES (%s, %s, %s) RETURNING token"
        )
        result = execute_query(query, (usuario_id, token, expires_at), fetch_one=True)
        return result["token"] if result else None

    @staticmethod
    def validate_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate a password reset token."""
        query = """
            SELECT usuario_id, token, utilizado FROM password_reset_tokens 
            WHERE token = %s 
            AND expira_en > NOW() 
            AND utilizado = FALSE
            LIMIT 1
        """
        return execute_query(query, (token,), fetch_one=True)

    @staticmethod
    def mark_reset_token_as_used(token: str) -> bool:
        """Mark a reset token as used."""
        query = (
            "UPDATE password_reset_tokens SET utilizado = TRUE, utilizado_en = NOW() "
            "WHERE token = %s"
        )
        execute_query(query, (token,))
        return True


class RoleService:
    @staticmethod
    def get_roles() -> List[Dict[str, Any]]:
        query = "SELECT id, nombre_rol, descripcion FROM roles"
        return execute_query(query, fetch_all=True)

    @staticmethod
    def create_role(nombre_rol: str, descripcion: str) -> Dict[str, Any]:
        query = (
            "INSERT INTO roles (nombre_rol, descripcion) "
            "VALUES (%s, %s) RETURNING id, nombre_rol, descripcion"
        )
        return execute_query(query, (nombre_rol, descripcion), fetch_one=True)

    @staticmethod
    def assign_role_to_user(usuario_id: int, rol_id: int) -> Dict[str, Any]:
        query = (
            "INSERT INTO usuarios_roles (usuario_id, rol_id) "
            "VALUES (%s, %s) RETURNING usuario_id, rol_id"
        )
        return execute_query(query, (usuario_id, rol_id), fetch_one=True)

    @staticmethod
    def assign_permission_to_role(rol_id: int, permiso_id: int) -> Dict[str, Any]:
        query = (
            "INSERT INTO roles_permisos (rol_id, permiso_id) "
            "VALUES (%s, %s) RETURNING rol_id, permiso_id"
        )
        return execute_query(query, (rol_id, permiso_id), fetch_one=True)

    @staticmethod
    def get_role_permissions(rol_id: int) -> List[Dict[str, Any]]:
        query = (
            "SELECT p.id, p.nombre_permiso, p.descripcion "
            "FROM permisos p "
            "JOIN roles_permisos rp ON p.id = rp.permiso_id "
            "WHERE rp.rol_id = %s"
        )
        return execute_query(query, (rol_id,), fetch_all=True) or []

    @staticmethod
    def remove_permission_from_role(rol_id: int, permiso_id: int) -> bool:
        query = "DELETE FROM roles_permisos WHERE rol_id = %s AND permiso_id = %s RETURNING rol_id, permiso_id"
        result = execute_query(query, (rol_id, permiso_id), fetch_one=True)
        return result is not None

    @staticmethod
    def update_role(rol_id: int, nombre_rol: str, descripcion: str) -> Optional[Dict[str, Any]]:
        query = (
            "UPDATE roles SET nombre_rol = %s, descripcion = %s "
            "WHERE id = %s RETURNING id, nombre_rol, descripcion"
        )
        return execute_query(query, (nombre_rol, descripcion, rol_id), fetch_one=True)

    @staticmethod
    def delete_role(rol_id: int) -> bool:
        query = "DELETE FROM roles WHERE id = %s RETURNING id"
        result = execute_query(query, (rol_id,), fetch_one=True)
        return result is not None


class PermissionService:
    @staticmethod
    def get_permissions() -> List[Dict[str, Any]]:
        query = "SELECT id, nombre_permiso, descripcion FROM permisos"
        return execute_query(query, fetch_all=True)

    @staticmethod
    def create_permission(nombre_permiso: str, descripcion: str) -> Dict[str, Any]:
        query = (
            "INSERT INTO permisos (nombre_permiso, descripcion) "
            "VALUES (%s, %s) RETURNING id, nombre_permiso, descripcion"
        )
        return execute_query(query, (nombre_permiso, descripcion), fetch_one=True)

    @staticmethod
    def update_permission(permiso_id: int, nombre_permiso: str, descripcion: str) -> Optional[Dict[str, Any]]:
        query = (
            "UPDATE permisos SET nombre_permiso = %s, descripcion = %s "
            "WHERE id = %s RETURNING id, nombre_permiso, descripcion"
        )
        return execute_query(query, (nombre_permiso, descripcion, permiso_id), fetch_one=True)

    @staticmethod
    def delete_permission(permiso_id: int) -> bool:
        query = "DELETE FROM permisos WHERE id = %s RETURNING id"
        result = execute_query(query, (permiso_id,), fetch_one=True)
        return result is not None


class SessionService:
    @staticmethod
    def get_active_sessions(usuario_id: int):
        query = (
            "SELECT token_jti, usuario_id, user_agent, creado_en, expira_en, revocado, revocado_en "
            "FROM sessions WHERE usuario_id = %s AND revocado = FALSE AND expira_en > NOW() ORDER BY creado_en DESC"
        )
        return execute_query(query, (usuario_id,), fetch_all=True)

    @staticmethod
    def get_session_by_jti(token_jti: str):
        query = "SELECT id, usuario_id, token_jti FROM sessions WHERE token_jti = %s LIMIT 1"
        return execute_query(query, (token_jti,), fetch_one=True)

    @staticmethod
    def revoke_all_sessions(usuario_id: int, reason: str = "logout_all") -> int:
        # Fetch JTIs for user
        rows = execute_query("SELECT token_jti FROM sessions WHERE usuario_id = %s AND revocado = FALSE", (usuario_id,), fetch_all=True)
        count = 0
        if rows:
            for r in rows:
                jti = r.get("token_jti")
                try:
                    # mark session revoked
                    execute_query(
                        "UPDATE sessions SET revocado = TRUE, revocado_en = NOW() WHERE token_jti = %s",
                        (jti,),
                    )
                    # add to blacklist
                    execute_query(
                        "INSERT INTO token_blacklist (token_jti, usuario_id, expira_en, razon) VALUES (%s, %s, %s, %s)",
                        (jti, usuario_id, datetime.datetime.utcnow() + datetime.timedelta(days=1), reason),
                    )
                    count += 1
                except Exception:
                    pass
        return count

    @staticmethod
    def revoke_session(jti: str, usuario_id: Optional[int] = None, reason: str = "logout") -> bool:
        try:
            execute_query("UPDATE sessions SET revocado = TRUE, revocado_en = NOW() WHERE token_jti = %s", (jti,))
            execute_query(
                "INSERT INTO token_blacklist (token_jti, usuario_id, expira_en, razon) VALUES (%s, %s, %s, %s)",
                (jti, usuario_id, datetime.datetime.utcnow() + datetime.timedelta(days=1), reason),
            )
            return True
        except Exception:
            return False

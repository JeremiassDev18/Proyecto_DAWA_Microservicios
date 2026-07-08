from flask import Blueprint, jsonify, request

from auth import authorize
from app.utils.audit import audit_log
from services import PermissionService, RoleService

permission_bp = Blueprint("permission_bp", __name__)


@permission_bp.route("/permisos", methods=["GET"])
@authorize(required_roles=["admin"], required_permissions=["read_users"])
def get_permissions():
    permisos = PermissionService.get_permissions()
    return jsonify({"permisos": permisos}), 200


@permission_bp.route("/permisos", methods=["POST"])
@audit_log("create_permission")
@authorize(required_roles=["admin"], required_permissions=["write_users"])
def create_permission():
    payload = request.get_json() or {}
    nombre_permiso = payload.get("nombre_permiso")
    descripcion = payload.get("descripcion")

    if not nombre_permiso:
        return jsonify({"error": "nombre_permiso es requerido"}), 400
    # attach audit details
    from flask import g
    g.audit_details = {"nombre_permiso": nombre_permiso}

    permission = PermissionService.create_permission(nombre_permiso, descripcion)
    return jsonify({"permiso": permission}), 201


@permission_bp.route("/permisos/<int:permiso_id>", methods=["PUT"])
@audit_log("update_permission")
@authorize(required_roles=["admin"], required_permissions=["write_users"])
def update_permission(permiso_id):
    payload = request.get_json() or {}
    nombre_permiso = payload.get("nombre_permiso")
    descripcion = payload.get("descripcion")

    if not nombre_permiso:
        return jsonify({"error": "nombre_permiso es requerido"}), 400

    from flask import g
    g.audit_details = {"permiso_id": permiso_id, "nombre_permiso": nombre_permiso}

    updated = PermissionService.update_permission(permiso_id, nombre_permiso, descripcion)
    if not updated:
        return jsonify({"error": "Permiso no encontrado"}), 404

    return jsonify({"permiso": updated}), 200


@permission_bp.route("/permisos/<int:permiso_id>", methods=["DELETE"])
@audit_log("delete_permission")
@authorize(required_roles=["admin"], required_permissions=["write_users"])
def delete_permission(permiso_id):
    from flask import g
    g.audit_details = {"permiso_id": permiso_id}

    deleted = PermissionService.delete_permission(permiso_id)
    if not deleted:
        return jsonify({"error": "Permiso no encontrado"}), 404
    return jsonify({"mensaje": "Permiso eliminado exitosamente"}), 200


@permission_bp.route("/roles/<int:rol_id>/permisos", methods=["GET"])
@authorize(required_roles=["admin"], required_permissions=["read_users"])
def get_permissions_for_role(rol_id):
    permisos = RoleService.get_role_permissions(rol_id)
    return jsonify({"permisos": permisos}), 200


@permission_bp.route("/roles/<int:rol_id>/permisos", methods=["POST"])
@audit_log("assign_permission_to_role")
@authorize(required_roles=["admin"], required_permissions=["write_users"])
def assign_permission_to_role(rol_id):
    payload = request.get_json() or {}
    permiso_id = payload.get("permiso_id")

    if not permiso_id:
        return jsonify({"error": "permiso_id es requerido"}), 400
    from flask import g
    g.audit_details = {"rol_id": rol_id, "permiso_id": permiso_id}

    assignment = RoleService.assign_permission_to_role(rol_id, permiso_id)
    return jsonify({"asignacion": assignment}), 201


@permission_bp.route("/roles/<int:rol_id>/permisos/<int:permiso_id>", methods=["DELETE"])
@audit_log("remove_permission_from_role")
@authorize(required_roles=["admin"], required_permissions=["write_users"])
def remove_permission_from_role(rol_id, permiso_id):
    from flask import g
    g.audit_details = {"rol_id": rol_id, "permiso_id": permiso_id}

    removed = RoleService.remove_permission_from_role(rol_id, permiso_id)
    if not removed:
        return jsonify({"error": "Permiso no encontrado para este rol"}), 404
    return jsonify({"mensaje": "Permiso removido del rol exitosamente"}), 200

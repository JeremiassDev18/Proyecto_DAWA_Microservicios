from functools import wraps
from flask import g, request
import json

from db import execute_query


def audit_log(action_type: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            response = fn(*args, **kwargs)

            try:
                user_id = getattr(g, "user_id", None) or getattr(g, "audit_user_id", None)
                remote_addr = request.remote_addr or request.headers.get("X-Forwarded-For", None)
                details = getattr(g, "audit_details", None) or {}
                details_json = json.dumps(details)
                # Insert structured details as JSONB
                execute_query(
                    "INSERT INTO auditoria (usuario_id, accion, direccion_ip, detalles) VALUES (%s, %s, %s, %s::jsonb)",
                    (user_id, action_type, remote_addr, details_json),
                )
            except Exception:
                # Audit should not break the main operation.
                pass

            return response

        return wrapper

    return decorator

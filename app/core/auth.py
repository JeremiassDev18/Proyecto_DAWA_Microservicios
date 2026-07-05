from fastapi import Header, HTTPException, Depends
from typing import Optional

from app.core.config import settings
from app.services.microservice_client import validar_token

INTERNAL_TOKEN = settings.INTERNAL_TOKEN


class AuthContext:
    def __init__(self, usuario_id: int, tipo: str, token: str):
        self.usuario_id = usuario_id
        self.tipo = tipo
        self.token = token

    @property
    def es_admin(self) -> bool:
        return self.tipo == "admin"

    @property
    def es_estudiante(self) -> bool:
        return self.tipo == "estudiante"


def verificar_token(authorization: Optional[str] = Header(None)) -> AuthContext:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.removeprefix("Bearer ").strip()

    if token == INTERNAL_TOKEN:
        return AuthContext(usuario_id=0, tipo="admin", token=token)

    user = validar_token(token)
    if user and user.get("valido"):
        return AuthContext(
            usuario_id=user["usuario_id"],
            tipo=user.get("tipo", "estudiante"),
            token=token,
        )

    raise HTTPException(status_code=401, detail="Token inválido o expirado")


def requerir_admin(auth: AuthContext = Depends(verificar_token)) -> AuthContext:
    if not auth.es_admin:
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador")
    return auth

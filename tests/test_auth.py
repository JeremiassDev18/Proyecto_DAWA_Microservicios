from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.core.auth import verificar_token, requerir_admin, AuthContext


def test_verificar_token_internal():
    ctx = verificar_token("Bearer internal_secret_token_xyz")
    assert ctx.es_admin
    assert ctx.usuario_id == 0


def test_verificar_token_estudiante():
    ctx = verificar_token("Bearer mock-token-estudiante")
    assert ctx.es_estudiante
    assert not ctx.es_admin
    assert ctx.usuario_id == 1


def test_verificar_token_invalido():
    with pytest.raises(HTTPException) as exc:
        verificar_token("Bearer token-falso")
    assert exc.value.status_code == 401


def test_verificar_token_sin_header():
    with pytest.raises(HTTPException) as exc:
        verificar_token(None)
    assert exc.value.status_code == 401


def test_requerir_admin_ok():
    ctx = AuthContext(usuario_id=0, tipo="admin", token="x")
    result = requerir_admin(auth=ctx)
    assert result is ctx


def test_requerir_admin_fail():
    ctx = AuthContext(usuario_id=1, tipo="estudiante", token="x")
    with pytest.raises(HTTPException) as exc:
        requerir_admin(auth=ctx)
    assert exc.value.status_code == 403

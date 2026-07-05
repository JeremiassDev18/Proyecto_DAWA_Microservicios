from app.services.microservice_client import (
    get_usuario, validar_token,
    crear_solicitud, buscar_docente, consultar_tutoria,
    cancelar_solicitud, escalar_docente, INTENT_SERVICE_MAP,
)


def test_get_usuario_existente():
    user = get_usuario(1)
    assert user is not None
    assert user["nombre"] == "Juan Pérez"


def test_get_usuario_inexistente():
    assert get_usuario(999) is None


def test_validar_token_valido():
    assert validar_token("mock-token-estudiante") is not None


def test_validar_token_invalido():
    assert validar_token("fake") is None


def test_crear_solicitud():
    sol = crear_solicitud(1, "Matemáticas", "Necesito ayuda")
    assert sol["codigo"].startswith("TUT-")
    assert sol["estado"] == "pendiente"
    assert sol["usuario_id"] == 1


def test_buscar_docente():
    results = buscar_docente("Matemáticas")
    assert len(results) >= 1
    assert results[0]["asignatura"] == "Matemáticas"


def test_buscar_docente_sin_resultados():
    results = buscar_docente("zzzzzzz")
    assert len(results) == 0


def test_consultar_tutoria():
    crear_solicitud(2, "Física", "Ayuda")
    tuts = consultar_tutoria(2)
    assert len(tuts) >= 1


def test_cancelar_solicitud():
    sol = crear_solicitud(1, "Química", "Cancel test")
    assert cancelar_solicitud(sol["id"]) is True
    assert cancelar_solicitud(9999) is False


def test_escalar_docente():
    sol = crear_solicitud(1, "Literatura", "Escalar test")
    result = escalar_docente(sol["id"])
    assert result["estado"] == "escalada"


def test_intent_service_map():
    assert "CREAR_SOLICITUD" in INTENT_SERVICE_MAP
    assert "BUSCAR_DOCENTE" in INTENT_SERVICE_MAP
    assert "CONSULTAR_MIS_TUTORIAS" in INTENT_SERVICE_MAP
    assert "SOLICITAR_TUTORIA" in INTENT_SERVICE_MAP

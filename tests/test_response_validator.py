from app.services.response_validator import validar_respuesta


def test_respuesta_valida():
    valido, motivo = validar_respuesta(
        "Las tutorías duran 60 minutos.",
        "¿Cuánto dura una tutoría?",
    )
    assert valido
    assert motivo is None


def test_respuesta_con_email():
    valido, motivo = validar_respuesta(
        "Puedes contactar al docente en jperez@unal.edu.pe",
        "¿Quién es el docente?",
    )
    assert not valido
    assert "información sensible" in motivo


def test_respuesta_con_dni():
    valido, motivo = validar_respuesta(
        "El DNI del estudiante es 12345678",
        "Datos del estudiante",
    )
    assert not valido
    assert "información sensible" in motivo


def test_respuesta_fuera_alcance():
    valido, motivo = validar_respuesta(
        "Te recomiendo la película El Padrino.",
        "Hola",
    )
    assert not valido
    assert "alcance institucional" in motivo


def test_texto_vacio():
    valido, motivo = validar_respuesta("", "consulta")
    assert valido
    assert motivo is None

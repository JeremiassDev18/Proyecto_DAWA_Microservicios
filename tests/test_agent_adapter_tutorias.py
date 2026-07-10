"""
Tests unitarios para TutoriasAdapter.

Mockea TutoriasRestClient y TutoriasClient para no depender de servicios externos.
"""

from unittest.mock import patch, MagicMock

from app.agent.adapters.tutorias import TutoriasAdapter


class TestConsultarMisTutorias:
    def test_sin_tutorias(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_client") as mock_get:
            mock_client = MagicMock()
            mock_client.consultar_mis_tutorias.return_value = []
            mock_get.return_value = mock_client

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_mis_tutorias(estudiante_id=1)

        assert "No tienes tutorías" in content
        assert state["ultima_accion"] == "consultar_tutorias"

    def test_con_tutorias(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_client") as mock_get:
            mock_client = MagicMock()
            mock_client.consultar_mis_tutorias.return_value = [
                {"id": 1, "tema": "Matemáticas", "estado": "asignada"},
                {"id": 2, "tema": "Programación", "estado": "solicitada"},
            ]
            mock_get.return_value = mock_client

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_mis_tutorias(estudiante_id=1)

        assert "Tus tutorías:" in content
        assert "Matemáticas" in content
        assert "Programación" in content
        assert state["ultima_tutoria"] == 2


class TestConsultarBitacorasResumidas:
    def test_sin_bitacoras(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = []
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante",
            )

        assert "No tienes bitácoras" in content
        assert state["ultima_accion"] == "consultar_bitacoras"

    def test_con_bitacoras(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = [
                {
                    "solicitud_id": 10,
                    "tema": "Álgebra",
                    "estado": "atendida",
                    "fecha_registro": "2025-06-01T10:00:00",
                    "observaciones": "Se explicaron matrices. Buen avance.",
                    "periodo_id": 2025,
                },
            ]
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante",
            )

        assert "Bitácoras de tutorías" in content
        assert "Álgebra" in content
        assert "#10" in content

    def test_por_solicitud_id(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_bitacoras_por_solicitud.return_value = [
                {
                    "solicitud_id": 4,
                    "observaciones": "Se resolvieron dudas de POO.",
                    "temas_detectados": "Polimorfismo, Herencia",
                    "fecha_registro": "2025-06-10T14:00:00",
                },
            ]
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, solicitud_id=4,
            )

        assert "tutoría #4" in content.lower()
        assert "POO" in content
        assert state["ultima_tutoria"] == 4

    def test_por_solicitud_id_sin_resultados(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_bitacoras_por_solicitud.return_value = []
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, solicitud_id=999,
            )

        assert "No se encontraron bitácoras" in content
        assert "999" in content

    def test_falla_bitacora_resumen_hace_rollback_y_cae_a_rest(self):
        """
        Cuando la tabla bitacora_resumen no existe, debe:
        1. Hacer rollback del db_conn
        2. Caer al REST client como fallback
        3. Devolver datos normales
        """
        from unittest.mock import PropertyMock

        with (
            patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get_rest,
            patch("app.db.queries.get_bitacora_resumenes_by_estudiante") as mock_query,
        ):
            # Simular tabla que no existe → error de BD
            mock_query.side_effect = Exception(
                'relation "bitacora_resumen" does not exist'
            )

            # Mock REST client devuelve datos reales
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = [
                {
                    "solicitud_id": 5,
                    "tema": "Base de datos",
                    "estado": "atendida",
                    "fecha_registro": "2025-06-15T09:00:00",
                    "observaciones": "Consultas SQL avanzadas.",
                    "periodo_id": 2025,
                },
            ]
            mock_get_rest.return_value = mock_rest

            # db_conn mock que verifica que se llame rollback
            mock_conn = MagicMock()
            mock_conn.rollback.return_value = None

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante", db_conn=mock_conn,
            )

        # Debe haber hecho rollback
        mock_conn.rollback.assert_called_once()

        # Debe haber caído al REST client
        assert "Bitácoras de tutorías" in content
        assert "Base de datos" in content
        assert "#5" in content

    def test_rollback_no_rompe_si_db_conn_es_none(self):
        """
        Cuando db_conn es None (porque no hay BD en el contexto),
        el except de bitacora_resumen no debe fallar al intentar rollback.
        """
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get_rest:
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = [
                {
                    "solicitud_id": 3,
                    "tema": "Cálculo",
                    "estado": "atendida",
                    "fecha_registro": "2025-06-10T11:00:00",
                    "observaciones": "Límites y derivadas.",
                    "periodo_id": 2025,
                },
            ]
            mock_get_rest.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante", db_conn=None,
            )

        assert "Bitácoras de tutorías" in content
        assert "Cálculo" in content
        assert state["total_bitacoras"] == 1

    def test_con_busqueda_filtra_por_tema(self):
        """Filtrar bitácoras por texto de materia/tema."""
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = [
                {"solicitud_id": 1, "tema": "Álgebra", "estado": "atendida",
                 "fecha_registro": "2025-06-01", "observaciones": "Matrices.", "periodo_id": 2025},
                {"solicitud_id": 2, "tema": "Programación", "estado": "atendida",
                 "fecha_registro": "2025-06-02", "observaciones": "POO.", "periodo_id": 2025},
                {"solicitud_id": 3, "tema": "Cálculo", "estado": "atendida",
                 "fecha_registro": "2025-06-03", "observaciones": "Límites.", "periodo_id": 2025},
            ]
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante", busqueda="programación",
            )

        assert "Programación" in content
        assert "Álgebra" not in content
        assert "Cálculo" not in content
        assert state["total_bitacoras"] == 1

    def test_con_busqueda_sin_resultados(self):
        """Filtrar bitácoras con busqueda que no coincide."""
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = [
                {"solicitud_id": 1, "tema": "Álgebra", "estado": "atendida",
                 "fecha_registro": "2025-06-01", "observaciones": "Matrices.", "periodo_id": 2025},
            ]
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante", busqueda="física",
            )

        assert "No se encontraron bitácoras" in content
        assert "física" in content.lower()
        assert state["ultima_busqueda"] == "física"

    def test_total_bitacoras_in_state(self):
        """El state debe incluir la cuenta total de bitácoras."""
        with patch("app.agent.adapters.tutorias.get_tutorias_rest_client") as mock_get:
            mock_rest = MagicMock()
            mock_rest.consultar_mis_bitacoras.return_value = [
                {"solicitud_id": i, "tema": f"Materia {i}", "estado": "atendida",
                 "fecha_registro": "2025-06-01", "observaciones": "...", "periodo_id": 2025}
                for i in range(1, 4)
            ]
            mock_get.return_value = mock_rest

            adapter = TutoriasAdapter()
            content, state = adapter.consultar_bitacoras_resumidas(
                estudiante_id=1, rol="estudiante",
            )

        assert state["total_bitacoras"] == 3


class TestCrearTutoria:
    def test_exitoso(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_client") as mock_get:
            mock_client = MagicMock()
            mock_client.registrar_solicitud.return_value = {
                "id": 42, "tema": "Cálculo", "estado": "solicitada",
            }
            mock_get.return_value = mock_client

            adapter = TutoriasAdapter()
            content, state = adapter.crear_tutoria(
                estudiante_id=1, asignatura_id=5, tema="Cálculo",
            )

        assert "Tutoría registrada" in content
        assert "42" in content
        assert state["ultima_tutoria"] == 42

    def test_fallido(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_client") as mock_get:
            mock_client = MagicMock()
            mock_client.registrar_solicitud.return_value = None
            mock_get.return_value = mock_client

            adapter = TutoriasAdapter()
            content, state = adapter.crear_tutoria(
                estudiante_id=1, asignatura_id=5, tema="Física",
            )

        assert "No se pudo registrar" in content


class TestCancelarTutoria:
    def test_exitoso(self):
        with patch("app.agent.adapters.tutorias.get_tutorias_client") as mock_get:
            mock_client = MagicMock()
            mock_client.cancelar_tutoria.return_value = {"estado": "cancelada"}
            mock_get.return_value = mock_client

            adapter = TutoriasAdapter()
            content, state = adapter.cancelar_tutoria(
                tutoria_id=10, motivo="Ya no la necesito", usuario_id=1,
            )

        assert "cancelada" in content
        assert "10" in content
        assert state["ultima_tutoria"] == 10

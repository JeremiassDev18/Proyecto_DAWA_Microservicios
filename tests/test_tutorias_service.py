import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.tutorias_service.database import Base
from backend.tutorias_service.service import TutoriasService

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


class TutoriasServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(bind=engine)

    def setUp(self) -> None:
        self.service = TutoriasService(db_session_factory=TestingSessionLocal)
        from backend.tutorias_service.models_db import SolicitudTutoria
        db = TestingSessionLocal()
        try:
            db.query(SolicitudTutoria).delete()
            db.commit()
        finally:
            db.close()

    def test_r01_registro_de_solicitud(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id=1,
            asignatura_id=10,
            periodo_id=5,
            tema="Álgebra",
            fecha_solicitud="2026-07-10T14:00:00",
        )

        self.assertEqual(tutoria["estado"], "solicitada")
        self.assertEqual(tutoria["tema"], "Álgebra")
        self.assertEqual(tutoria["estudiante_id"], 1)
        self.assertEqual(tutoria["asignatura_id"], 10)
        self.assertEqual(tutoria["periodo_id"], 5)

    def test_r02_validacion_de_disponibilidad(self) -> None:
        self.assertTrue(self.service.validar_disponibilidad_docente("D001", "2026-07-10"))

    def test_r03_asignacion_a_docente(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id=2,
            tema="Diseño",
            fecha_solicitud="2026-07-11T16:00:00",
        )

        resultado = self.service.asignar_tutoria(tutoria["id"], 1)

        self.assertTrue(resultado["asignada"])
        self.assertEqual(resultado["docente_id"], 1)

    def test_r04_confirmacion_y_cancelacion(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id=3,
            tema="Finanzas",
            fecha_solicitud="2026-07-12T10:00:00",
        )

        confirmada = self.service.confirmar_o_cancelar_tutoria(
            tutoria["id"], "confirmar",
            usuario_id="3", rol_usuario="estudiante",
        )
        self.assertEqual(confirmada["estado"], "confirmada")

        cancelada = self.service.confirmar_o_cancelar_tutoria(
            tutoria["id"], "cancelar",
            motivo="El estudiante no asistirá",
            usuario_id="3", rol_usuario="estudiante",
        )
        self.assertEqual(cancelada["estado"], "cancelada")
        self.assertEqual(cancelada["motivo_cancelacion"], "El estudiante no asistirá")

    def test_r05_registro_de_asistencia(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id=4,
            tema="Ética",
            fecha_solicitud="2026-07-10T12:00:00",
        )
        self.service.asignar_tutoria(tutoria["id"], 1)

        asistencia = self.service.registrar_asistencia_estudiante(tutoria["id"], True)

        self.assertTrue(asistencia["asistio"])

    def test_r06_r07_r08_r12(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id=5,
            tema="Fisiología",
            fecha_solicitud="2026-07-10T08:30:00",
        )
        self.service.registrar_bitacora_atencion(
            tutoria["id"],
            "Se revisó el tema de fisiología",
            usuario_id="5",
        )
        self.service.gestionar_estado_tutoria(
            tutoria["id"], "en_proceso",
            usuario_id="5", rol_usuario="docente",
        )
        self.service.registrar_seguimiento_caso_academico("5", "Bajo rendimiento", "alto")
        notificacion = self.service.notificar_cambio_estado(
            tutoria["id"], "en_proceso",
            destinatario_id=5,
        )

        obtenida = self.service.obtener_tutoria(tutoria["id"])
        self.assertEqual(obtenida["estado"], "en_proceso")
        self.assertEqual(notificacion["mensaje"], "Cambio de estado en tutoría #{}: en_proceso".format(tutoria["id"]))

    def test_r09_r10_r11_reportes(self) -> None:
        t1 = self.service.registrar_solicitud_tutoria(1, tema="Álgebra", fecha_solicitud="2026-07-10T09:00:00")
        t2 = self.service.registrar_solicitud_tutoria(1, tema="Álgebra", fecha_solicitud="2026-07-10T11:00:00")
        t3 = self.service.registrar_solicitud_tutoria(2, tema="Fisiología", fecha_solicitud="2026-07-11T13:00:00")

        for t in [t1, t2, t3]:
            self.service.asignar_tutoria(t["id"], 1)
            self.service.registrar_asistencia_estudiante(t["id"], True)

        reporte_docente = self.service.generar_reporte_tutorias_por_docente(1)
        reporte_estudiantes = self.service.generar_reporte_estudiantes_atendidos()
        reporte_temas = self.service.generar_reporte_temas_recurrentes()

        self.assertEqual(reporte_docente["docente_id"], 1)
        self.assertEqual(reporte_docente["cantidad"], 3)
        self.assertEqual(reporte_estudiantes["cantidad"], 2)
        self.assertIn("Álgebra", reporte_temas["temas"])


if __name__ == "__main__":
    unittest.main()

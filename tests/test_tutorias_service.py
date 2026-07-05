import unittest

from backend.tutorias_service.service import TutoriasService


class TutoriasServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TutoriasService()
        self.service.registrar_docente("D001", "Ana", ["2026-07-10", "2026-07-11"])
        self.service.registrar_docente("D002", "Luis", ["2026-07-12"])

    def test_r01_registro_de_solicitud(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id="E001",
            carrera="Ingeniería de Sistemas",
            tema="Álgebra",
            fecha_solicitud="2026-07-10",
            hora_solicitud="14:00",
        )

        self.assertEqual(tutoria["estado"], "solicitada")
        self.assertEqual(tutoria["tema"], "Álgebra")
        self.assertEqual(tutoria["estudiante_id"], "E001")

    def test_r02_validacion_de_disponibilidad(self) -> None:
        self.assertTrue(self.service.validar_disponibilidad_docente("D001", "2026-07-10"))
        self.assertFalse(self.service.validar_disponibilidad_docente("D001", "2026-07-20"))

    def test_r03_asignacion_a_docente(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id="E002",
            carrera="Arquitectura",
            tema="Diseño",
            fecha_solicitud="2026-07-11",
            hora_solicitud="16:00",
        )

        resultado = self.service.asignar_tutoria(tutoria["id"], "D001")

        self.assertTrue(resultado["asignada"])
        self.assertEqual(resultado["docente_id"], "D001")

    def test_r04_confirmacion_y_cancelacion(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id="E003",
            carrera="Contabilidad",
            tema="Finanzas",
            fecha_solicitud="2026-07-12",
            hora_solicitud="10:00",
        )

        confirmada = self.service.confirmar_o_cancelar_tutoria(tutoria["id"], "confirmar")
        self.assertEqual(confirmada["estado"], "confirmada")

        cancelada = self.service.confirmar_o_cancelar_tutoria(tutoria["id"], "cancelar", "El estudiante no asistirá")
        self.assertEqual(cancelada["estado"], "cancelada")

    def test_r05_registro_de_asistencia(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id="E004",
            carrera="Derecho",
            tema="Ética",
            fecha_solicitud="2026-07-10",
            hora_solicitud="12:00",
        )
        self.service.asignar_tutoria(tutoria["id"], "D001")

        asistencia = self.service.registrar_asistencia_estudiante(tutoria["id"], True)

        self.assertTrue(asistencia["asistio"])

    def test_r06_r07_r08_r12(self) -> None:
        tutoria = self.service.registrar_solicitud_tutoria(
            estudiante_id="E005",
            carrera="Medicina",
            tema="Fisiología",
            fecha_solicitud="2026-07-10",
            hora_solicitud="08:30",
        )
        self.service.registrar_bitacora_atencion(tutoria["id"], "Se revisó el tema de fisiología")
        self.service.gestionar_estado_tutoria(tutoria["id"], "en_proceso")
        self.service.registrar_seguimiento_caso_academico("E005", "Bajo rendimiento", "alto")
        notificacion = self.service.notificar_cambio_estado(tutoria["id"], "en_proceso")

        self.assertEqual(len(self.service.obtener_tutoria(tutoria["id"])["bitacora"]), 1)
        self.assertEqual(self.service.obtener_tutoria(tutoria["id"])["estado"], "en_proceso")
        self.assertEqual(notificacion["mensaje"], "Cambio de estado: en_proceso")

    def test_r09_r10_r11_reportes(self) -> None:
        tutorias = [
            self.service.registrar_solicitud_tutoria("E010", "Ingeniería", "Álgebra", "2026-07-10", "09:00"),
            self.service.registrar_solicitud_tutoria("E011", "Ingeniería", "Álgebra", "2026-07-10", "11:00"),
            self.service.registrar_solicitud_tutoria("E012", "Medicina", "Fisiología", "2026-07-11", "13:00"),
        ]
        for tutoria in tutorias:
            self.service.asignar_tutoria(tutoria["id"], "D001")
            self.service.registrar_asistencia_estudiante(tutoria["id"], True)

        reporte_docente = self.service.generar_reporte_tutorias_por_docente("D001")
        reporte_estudiantes = self.service.generar_reporte_estudiantes_atendidos()
        reporte_temas = self.service.generar_reporte_temas_recurrentes()

        self.assertEqual(reporte_docente["docente_id"], "D001")
        self.assertEqual(reporte_estudiantes["cantidad"], 3)
        self.assertIn("Álgebra", reporte_temas["temas"])


if __name__ == "__main__":
    unittest.main()

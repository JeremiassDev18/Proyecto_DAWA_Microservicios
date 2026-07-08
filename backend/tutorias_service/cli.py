from __future__ import annotations

from .service import TutoriasService


def main() -> None:
    service = TutoriasService()
    service.registrar_docente("D001", "Ana", ["2026-07-10", "2026-07-11"])
    tutoria = service.registrar_solicitud_tutoria(
        estudiante_id="E001",
        carrera="Ingeniería de Sistemas",
        tema="Álgebra",
        fecha_solicitud="2026-07-10",
        hora_solicitud="14:00",
    )
    service.asignar_tutoria(tutoria["id"], "D001")
    service.registrar_asistencia_estudiante(tutoria["id"], True)
    print(tutoria)


if __name__ == "__main__":
    main()

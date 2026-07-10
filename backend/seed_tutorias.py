"""
Seed script: populate tutorias_db with realistic tutoring data.

Run inside the tutorias-service container or directly against PostgreSQL:
    docker compose exec tutorias-service python seed_tutorias.py

Or locally if DATABASE_URL_TUTORIAS is set.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent dir so we can import the service modules
sys.path.insert(0, os.path.dirname(__file__))

from tutorias_service.database import Base
from tutorias_service.models_db import (
    AuditoriaTutoria,
    BitacoraAtencion,
    HistorialEstado,
    InscripcionSesion,
    Notificacion,
    SesionTutoria,
    SolicitudTutoria,
)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed():
    db_url = os.getenv(
        "DATABASE_URL_TUTORIAS",
        "postgresql://postgres:password@localhost:5434/tutorias_db",
    )
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = Session()

    # Check if already seeded
    existing = db.query(SolicitudTutoria).count()
    if existing > 0:
        print(f"Database already has {existing} solicitudes. Skipping seed.")
        db.close()
        return

    print("Seeding tutorias database...")

    # Reference IDs (from administracion DB):
    # estudiante_id=1  (usuario_id=3), estudiante_id=2, estudiante_id=3
    # docente_id=1, docente_id=2
    # asignatura_id=1 (Cálculo I), asignatura_id=2 (Álgebra Lineal)
    # periodo_id=1

    base_date = _now() - timedelta(days=30)

    # ═══════════════════════════════════════════════════════════════
    # 1. Solicitudes de estudiantes → accept → sessions
    # ═══════════════════════════════════════════════════════════════

    solicitudes_data = [
        # (estudiante_id, asignatura_id, tema, estado, docente_id, days_ago)
        (1, 1, "Derivadas y regla de la cadena", "confirmada", 1, 28),
        (2, 1, "Integrales definidas y propiedades", "confirmada", 1, 25),
        (3, 2, "Espacios vectoriales y base", "confirmada", 2, 22),
        (1, 2, "Valores propios y vectores propios", "sin_asignar", None, 20),
        (2, 1, "Sucesiones y series numéricas", "solicitada", None, 5),
        (3, 1, "Límites y continuidad", "solicitada", None, 3),
        (1, 1, "Ecuaciones diferenciales ordinarias", "atendida", 1, 28),
        (2, 2, "Transformaciones lineales", "atendida", 2, 20),
        (3, 1, "Matrices y operaciones", "cancelada", None, 15),
    ]

    solicitudes = []
    for est_id, asig_id, tema, estado, doc_id, days in solicitudes_data:
        s = SolicitudTutoria(
            estudiante_id=est_id,
            docente_id=doc_id,
            asignatura_id=asig_id,
            periodo_id=1,
            tema=tema,
            estado=estado,
            fecha_solicitud=base_date + timedelta(days=days),
            fecha_agendada=(base_date + timedelta(days=days + 2)) if estado == "confirmada" else None,
            fecha_actualizacion=base_date + timedelta(days=days),
            motivo_cancelacion="No puedo asistir" if estado == "cancelada" else None,
        )
        db.add(s)
        db.flush()
        solicitudes.append(s)

    print(f"  Created {len(solicitudes)} solicitudes")

    # ═══════════════════════════════════════════════════════════════
    # 2. Sesiones for confirmed solicitudes
    # ═══════════════════════════════════════════════════════════════

    sesiones_data = [
        # (solicitud_idx, docente_id, asignatura_id, tema, estado, inscritos, days_ago)
        (0, 1, 1, "Derivadas y regla de la cadena", "atendida", 3, 26),
        (1, 1, 1, "Integrales definidas y propiedades", "en_curso", 2, 23),
        (2, 2, 2, "Espacios vectoriales y base", "abierta", 1, 20),
        (6, 1, 1, "Ecuaciones diferenciales ordinarias", "atendida", 4, 26),
    ]

    sesiones = []
    for sol_idx, doc_id, asig_id, tema, estado, inscritos, days in sesiones_data:
        sol = solicitudes[sol_idx]
        sesion = SesionTutoria(
            solicitud_id=sol.id,
            docente_id=doc_id,
            asignatura_id=asig_id,
            tema=tema,
            descripcion=f"Sesión grupal de tutoría sobre {tema}",
            estado=estado,
            fecha_creacion=base_date + timedelta(days=days),
            fecha_agendada=base_date + timedelta(days=days + 1),
            fecha_inicio=(base_date + timedelta(days=days + 1, hours=1)) if estado in ("en_curso", "atendida") else None,
            fecha_fin=(base_date + timedelta(days=days + 1, hours=2)) if estado == "atendida" else None,
            capacidad_maxima=20,
            total_inscritos=inscritos,
        )
        db.add(sesion)
        db.flush()
        sesiones.append(sesion)
        sol.sesion_id = sesion.id

    print(f"  Created {len(sesiones)} sesiones")

    # ═══════════════════════════════════════════════════════════════
    # 3. Inscripciones (students join sessions)
    # ═══════════════════════════════════════════════════════════════

    inscripciones_data = [
        # (sesion_idx, estudiante_id, asistio)
        (0, 1, True),
        (0, 2, True),
        (0, 3, False),
        (1, 1, None),
        (1, 2, None),
        (2, 3, None),
        (3, 1, True),
        (3, 2, True),
        (3, 3, True),
        (3, 1, True),  # duplicate handled by check
    ]

    for ses_idx, est_id, asistio in inscripciones_data:
        sesion = sesiones[ses_idx]
        # Skip duplicates
        exists = db.query(InscripcionSesion).filter(
            InscripcionSesion.sesion_id == sesion.id,
            InscripcionSesion.estudiante_id == est_id,
        ).first()
        if exists:
            continue
        ins = InscripcionSesion(
            sesion_id=sesion.id,
            estudiante_id=est_id,
            fecha_inscripcion=sesion.fecha_creacion + timedelta(hours=1),
            asistio=asistio,
        )
        db.add(ins)

    print("  Created inscripciones")

    # ═══════════════════════════════════════════════════════════════
    # 4. Bitácoras (logs from attended sessions)
    # ═══════════════════════════════════════════════════════════════

    bitacoras_data = [
        # (solicitud_idx, observaciones, asistio, temas_detectados)
        (0, "Se revisaron ejercicios de derivadas compuestas. El estudiante mejoró su comprensión.", True, "Derivadas, Regla de la cadena"),
        (6, "Ecuaciones de primer y segundo orden. Se resolvieron 5 ejercicios pratcicos.", True, "EDO, Métodos de resolución"),
        (7, "Introducción a espacios vectoriales. Se trabajó con bases y dimensiones.", True, "Álgebra lineal, Espacios vectoriales"),
    ]

    for sol_idx, obs, asistio, temas in bitacoras_data:
        b = BitacoraAtencion(
            solicitud_id=solicitudes[sol_idx].id,
            observaciones=obs,
            asistio=asistio,
            temas_detectados=temas,
            fecha_registro=base_date + timedelta(days=28, hours=3),
        )
        db.add(b)

    print("  Created bitácoras")

    # ═══════════════════════════════════════════════════════════════
    # 5. Historial de estados
    # ═══════════════════════════════════════════════════════════════

    for sol in solicitudes:
        h = HistorialEstado(
            solicitud_id=sol.id,
            estado_anterior=None,
            estado_nuevo=sol.estado,
            usuario_id=str(sol.estudiante_id),
            rol_usuario="estudiante",
            fecha_cambio=sol.fecha_solicitud,
            comentario="Solicitud creada",
        )
        db.add(h)

    print("  Created historial")

    # ═══════════════════════════════════════════════════════════════
    # 6. Auditoría
    # ═══════════════════════════════════════════════════════════════

    for i, sol in enumerate(solicitudes):
        a = AuditoriaTutoria(
            usuario_id=str(sol.estudiante_id),
            accion="CREAR_SOLICITUD",
            modulo="TUTORIAS",
            descripcion=f"Solicitud #{sol.id} creada: {sol.tema}",
            fecha=sol.fecha_solicitud,
        )
        db.add(a)

    print("  Created auditoría")

    db.commit()
    print("\n✅ Seed complete! Database populated with realistic tutoring data.")
    print(f"   - {len(solicitudes)} solicitudes")
    print(f"   - {len(sesiones)} sesiones")
    print(f"   - 10 inscripciones")
    print(f"   - {len(bitacoras_data)} bitácoras")
    print(f"   - {len(solicitudes)} historial entries")
    print(f"   - {len(solicitudes)} auditoría entries")

    db.close()


if __name__ == "__main__":
    seed()

from app.database import SessionLocal
from app.models import AuditoriaAdministracion


def registrar_auditoria(usuario_id, accion, modulo, descripcion):
    db = SessionLocal()
    try:
        registro = AuditoriaAdministracion(
            usuario_id=usuario_id,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion
        )

        db.add(registro)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error registrando auditoría: {e}")
    finally:
        db.close()
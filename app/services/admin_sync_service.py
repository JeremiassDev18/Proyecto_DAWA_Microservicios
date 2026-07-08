import os
from typing import Optional

from app.core.config import settings
from app.db import queries
from app.db.postgres_client import get_connection, release_connection
from app.db.training_repository import get_training_data
from app.ml.vectorizer import generate_embedding
from app.services.microservice_client import get_admin_client
from app.services.training_queue import enqueue_training
from app.utils.logger import logger

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "scripts", "data",
)

DOCENTE_INTENT = "BUSCAR_DOCENTE"
PERFIL_INTENT = "CONSULTAR_PERFIL"
SIN_INTENT = "SIN_INTENCION"
RAG_FUENTE = "auto-sync"


def _load_templates(filename: str) -> list[str]:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logger.warning(f"Templates file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and "{}" in line]


def _load_hard_negatives() -> list[str]:
    path = os.path.join(DATA_DIR, "hard_negatives.txt")
    if not os.path.exists(path):
        logger.warning(f"Hard negatives file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _ejemplo_ya_existe(conn, texto: str, id_intencion: int) -> bool:
    row = queries.query_dataset(conn, texto_query=texto)
    if not row:
        return False
    for r in row:
        if r[2] == id_intencion:
            return True
    return False


def _insertar_ejemplo(conn, texto: str, id_intencion: int) -> bool:
    if _ejemplo_ya_existe(conn, texto, id_intencion):
        return False
    embedding = generate_embedding(texto)
    ds_id = queries.insert_dataset(conn, texto, id_intencion, embedding, origen="auto")
    queries.validate_dataset(conn, ds_id)
    return True


def sync() -> dict:
    conn = None
    try:
        conn = get_connection()
        admin = get_admin_client()

        stats = {
            "docentes_encontrados": 0,
            "carreras_encontradas": 0,
            "facultades_encontradas": 0,
            "ejemplos_generados": 0,
            "ejemplos_insertados": 0,
            "duplicados_omitidos": 0,
            "documentos_rag_generados": 0,
            "training_task_id": None,
            "errores": [],
        }

        # ── 1. Obtener datos de administración ─────────────────────────
        docentes = admin.buscar_docentes()
        if not isinstance(docentes, list):
            docentes = []
        stats["docentes_encontrados"] = len(docentes)

        carreras = admin.get_carreras()
        if not isinstance(carreras, list):
            carreras = []
        stats["carreras_encontradas"] = len(carreras)

        facultades = []
        if hasattr(admin, "get_facultades"):
            facultades = admin.get_facultades()
        if not isinstance(facultades, list):
            facultades = []
        stats["facultades_encontradas"] = len(facultades)

        # ── 2. Cargar templates ───────────────────────────────────────
        templates_docente = _load_templates("templates_docente.txt")
        templates_carrera = _load_templates("templates_carrera.txt")
        templates_facultad = _load_templates("templates_facultad.txt")
        hard_negatives = _load_hard_negatives()

        # ── 3. IDs de intenciones ─────────────────────────────────────
        id_buscar_docente = queries.get_or_create_intencion(conn, DOCENTE_INTENT)
        id_perfil = queries.get_or_create_intencion(conn, PERFIL_INTENT)
        id_sin_intencion = queries.get_or_create_intencion(conn, SIN_INTENT)

        # ── 4. Generar ejemplos desde docentes reales ─────────────────
        docentes_set = set()
        for d in docentes:
            nombre = d.get("nombre") or d.get("nombres", "")
            apellidos = d.get("apellidos", "")
            full_name = f"{nombre} {apellidos}".strip()
            if not full_name:
                continue
            docentes_set.add(full_name)

        for d in docentes_set:
            for template in templates_docente:
                texto = template.format(d)
                stats["ejemplos_generados"] += 1
                if _insertar_ejemplo(conn, texto, id_buscar_docente):
                    stats["ejemplos_insertados"] += 1
                else:
                    stats["duplicados_omitidos"] += 1

        # ── 5. Generar ejemplos desde carreras reales ─────────────────
        carreras_por_facultad: dict[str, list[str]] = {}
        for c in carreras:
            nombre_carrera = c.get("nombre", "")
            if not nombre_carrera:
                continue
            facultad_nombre = c.get("facultad_nombre") or c.get("facultad", "")
            if facultad_nombre not in carreras_por_facultad:
                carreras_por_facultad[facultad_nombre] = []
            carreras_por_facultad[facultad_nombre].append(nombre_carrera)

        for facultad_nombre, carreras_list in carreras_por_facultad.items():
            if not facultad_nombre:
                continue
            for template in templates_carrera:
                texto = template.format(facultad_nombre)
                stats["ejemplos_generados"] += 1
                if _insertar_ejemplo(conn, texto, id_perfil):
                    stats["ejemplos_insertados"] += 1
                else:
                    stats["duplicados_omitidos"] += 1

        # ── 6. Generar ejemplos desde facultades reales ───────────────
        for f in facultades:
            nombre_facultad = f.get("nombre", "")
            codigo = f.get("codigo", "")
            label = codigo if codigo else nombre_facultad
            if not label:
                continue
            for template in templates_facultad:
                texto = template.format(label)
                stats["ejemplos_generados"] += 1
                if _insertar_ejemplo(conn, texto, id_perfil):
                    stats["ejemplos_insertados"] += 1
                else:
                    stats["duplicados_omitidos"] += 1

        # ── 7. Hard negatives ─────────────────────────────────────────
        for nombre in hard_negatives:
            for template in templates_docente:
                texto = template.format(nombre)
                stats["ejemplos_generados"] += 1
                if _insertar_ejemplo(conn, texto, id_sin_intencion):
                    stats["ejemplos_insertados"] += 1
                else:
                    stats["duplicados_omitidos"] += 1

        # ── 8. Reconstruir documentos RAG ─────────────────────────────
        stats["documentos_rag_generados"] = _rebuild_rag(conn, docentes, carreras, facultades)

        # ── 9. Entrenar si hubo cambios ───────────────────────────────
        if stats["ejemplos_insertados"] > 0:
            texts, labels = get_training_data(conn)
            if texts:
                task_id = enqueue_training(texts, labels)
                stats["training_task_id"] = task_id
                if task_id is None:
                    logger.info("Sync: training skipped, already in progress")
                else:
                    logger.info(f"Sync: training enqueued task_id={task_id}")
            else:
                logger.warning("Sync: no training data available after insert")

        logger.info(f"Sync completed: {stats['ejemplos_insertados']} nuevos, "
                     f"{stats['duplicados_omitidos']} duplicados, "
                     f"{stats['documentos_rag_generados']} docs RAG, "
                     f"training={'encolado' if stats['training_task_id'] else 'ninguno'}")

        return stats

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {
            "error": str(e),
            "docentes_encontrados": 0,
            "carreras_encontradas": 0,
            "facultades_encontradas": 0,
            "ejemplos_generados": 0,
            "ejemplos_insertados": 0,
            "duplicados_omitidos": 0,
            "documentos_rag_generados": 0,
            "training_task_id": None,
        }
    finally:
        if conn:
            release_connection(conn)


def _rebuild_rag(conn, docentes: list[dict], carreras: list[dict], facultades: list[dict]) -> int:
    if not docentes and not carreras and not facultades:
        logger.warning("RAG rebuild: no data available")
        return 0

    queries.desactivar_documentos_por_fuente(conn, RAG_FUENTE)
    count = 0

    if docentes:
        lines = ["Docentes disponibles:"]
        for d in docentes:
            nombre = d.get("nombre") or d.get("nombres", "")
            apellidos = d.get("apellidos", "")
            especialidad = d.get("especialidad", "")
            facultad = d.get("facultad_nombre") or d.get("facultad", "")
            entry = f"- {nombre} {apellidos}".strip()
            if especialidad:
                entry += f" ({especialidad})"
            if facultad:
                entry += f" - {facultad}"
            lines.append(entry)

        contenido = "\n".join(lines)
        embedding = generate_embedding(contenido)
        queries.insert_documento(conn, "Directorio de Docentes", contenido,
                                 embedding, categoria="docentes", fuente=RAG_FUENTE)
        count += 1

    if carreras:
        por_facultad: dict[str, list[str]] = {}
        for c in carreras:
            fac = c.get("facultad_nombre") or c.get("facultad", "General")
            if fac not in por_facultad:
                por_facultad[fac] = []
            nombre = c.get("nombre", "")
            codigo = c.get("codigo", "")
            label = f"{nombre} ({codigo})" if codigo else nombre
            por_facultad[fac].append(label)

        lines = ["Catálogo de Carreras por Facultad:"]
        for fac, carr_list in sorted(por_facultad.items()):
            lines.append(f"\n{fac}:")
            for c in sorted(carr_list):
                lines.append(f"  - {c}")

        contenido = "\n".join(lines)
        embedding = generate_embedding(contenido)
        queries.insert_documento(conn, "Catálogo de Carreras por Facultad", contenido,
                                 embedding, categoria="carreras", fuente=RAG_FUENTE)
        count += 1

    if facultades:
        lines = ["Facultades:"]
        for f in facultades:
            nombre = f.get("nombre", "")
            codigo = f.get("codigo", "")
            descripcion = f.get("descripcion", "")
            entry = f"- {nombre} ({codigo})" if codigo else f"- {nombre}"
            if descripcion:
                entry += f": {descripcion}"
            lines.append(entry)

        contenido = "\n".join(lines)
        embedding = generate_embedding(contenido)
        queries.insert_documento(conn, "Estructura Académica - Facultades", contenido,
                                 embedding, categoria="facultades", fuente=RAG_FUENTE)
        count += 1

    logger.info(f"RAG rebuild: {count} documentos generados")
    return count

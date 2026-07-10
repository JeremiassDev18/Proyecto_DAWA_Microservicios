"""
Adaptador RAG para el agente LLM.

Recupera conocimiento institucional mediante búsqueda híbrida
(pgvector + pg_trgm), filtra por score mínimo y devuelve el
texto formateado para que el LLM lo interprete.
"""

from app.core.config import settings
from app.db import queries
from app.ml.vectorizer import generate_embedding
from app.agent.ollama_client import OllamaClient
from app.utils.logger import logger


class RAGAdapter:
    """Adaptador de búsqueda en centro de conocimiento."""

    def __init__(self):
        self.ollama = OllamaClient()

    def buscar_conocimiento(
        self,
        conn,
        consulta: str,
        top_k: int | None = None,
        return_scores: bool = False,
    ) -> list[dict] | tuple[list[dict], list[float]]:
        """
        Busca conocimiento relevante y devuelve los documentos filtrados por score.

        Args:
            conn: conexión a PostgreSQL.
            consulta: texto de la consulta del usuario.
            top_k: cantidad final de documentos a devolver.
            return_scores: si True, devuelve también la lista de scores.

        Returns:
            Lista de dicts con titulo, contenido, score.
            Si return_scores=True, devuelve (documentos, scores).
        """
        top_k = top_k or settings.RAG_TOP_K
        candidatos = settings.RAG_CANDIDATES
        min_score = settings.RAG_MIN_SCORE

        logger.info(f"[RAG] consulta='{consulta}' candidatos={candidatos} min_score={min_score}")

        embedding = generate_embedding(consulta)
        rows = queries.search_conocimiento_hibrido(
            conn, consulta, embedding,
            limit=candidatos,
            vector_weight=settings.RAG_VECTOR_WEIGHT,
            trgm_weight=settings.RAG_TEXT_WEIGHT,
        )

        if not rows:
            logger.info("[RAG] sin resultados")
            if return_scores:
                return [], []
            return []

        # Filtrar por score mínimo y quedarse con los top_k mejores.
        filtrados = [r for r in rows if float(r[3]) >= min_score]
        filtrados = filtrados[:top_k]

        scores = [float(r[3]) for r in filtrados]
        documentos = [
            {"titulo": r[1], "contenido": r[2], "score": float(r[3])}
            for r in filtrados
        ]

        logger.info(
            f"[RAG] docs_filtrados={len(documentos)} (de {len(rows)} candidatos) "
            f"scores={[round(s, 3) for s in scores]}"
        )

        if return_scores:
            return documentos, scores
        return documentos

    def format_context(self, documentos: list[dict]) -> str:
        """Formatea los documentos como contexto para el LLM."""
        if not documentos:
            return "No hay contexto disponible."

        partes = ["Contexto disponible:"]
        for i, doc in enumerate(documentos, start=1):
            partes.append(f"Documento {i}")
            partes.append(f"Título: {doc['titulo']}")
            partes.append(f"Contenido: {doc['contenido']}")
            partes.append("")

        partes.append(
            "Si el contexto no responde la pregunta del usuario, "
            "indica claramente que no existe información suficiente."
        )
        return "\n".join(partes)

    def responder_con_contexto(self, consulta: str, documentos: list[dict]) -> str:
        """Genera una respuesta del LLM usando únicamente el contexto recuperado."""
        contexto = self.format_context(documentos)
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente universitario. Responde la pregunta del usuario "
                    "usando ÚNICAMENTE la información del contexto proporcionado. "
                    "Si el contexto no contiene la respuesta, di que no tienes información suficiente."
                ),
            },
            {"role": "user", "content": f"{contexto}\n\nPregunta del usuario: {consulta}"},
        ]

        raw = self.ollama.chat(messages)
        return raw.content if raw else "No pude generar una respuesta con el contexto disponible."

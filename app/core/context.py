from contextvars import ContextVar

estudiante_id_ctx: ContextVar[int | None] = ContextVar("estudiante_id", default=None)


def get_estudiante_id() -> int | None:
    return estudiante_id_ctx.get()

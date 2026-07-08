from fastapi import APIRouter, Depends, HTTPException, Query

from app.controllers import document_controller as ctrl
from app.core.dependencies import get_db
from app.core.auth import requerir_admin
from app.schemas.requests import DocumentCreate, DocumentUpdate
from app.schemas.responses import DocumentListResponse, DocumentResponse
from app.utils.logger import logger
from app.utils.pagination import paginate

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    query: str = Query("", description="Search by title or content"),
    categoria: str = Query("", description="Filter by category"),
    activo: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
    _auth=Depends(requerir_admin),
):
    items = ctrl.list_documents(conn, texto_query=query, categoria=categoria, activo=activo)
    paged, total = paginate(items, page, page_size)
    return DocumentListResponse(items=[DocumentResponse(**i) for i in paged], total=total)


@router.get("/documents/{id}", response_model=DocumentResponse)
def get_document(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    item = ctrl.get_document(conn, id)
    if not item:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return DocumentResponse(**item)


@router.post("/documents", response_model=DocumentResponse, status_code=201)
def create_document(req: DocumentCreate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    item = ctrl.create_document(
        conn, req.titulo, req.contenido,
        req.categoria, req.fuente, req.archivo_pdf,
    )
    logger.info(f"Documento creado id={item['id']}: {req.titulo}")
    return DocumentResponse(**item)


@router.put("/documents/{id}", response_model=DocumentResponse)
def update_document(id: int, req: DocumentUpdate, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    item = ctrl.update_document(
        conn, id, req.titulo, req.contenido,
        req.categoria, req.fuente, req.archivo_pdf,
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    logger.info(f"Documento actualizado id={id}")
    return DocumentResponse(**item)


@router.delete("/documents/{id}")
def delete_document(id: int, conn=Depends(get_db), _auth=Depends(requerir_admin)):
    ok = ctrl.delete_document(conn, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"mensaje": "Documento desactivado", "id": id}

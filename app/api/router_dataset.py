from fastapi import APIRouter, Depends, HTTPException, Query

from app.controllers import dataset_controller as ctrl
from app.core.dependencies import get_db
from app.schemas.requests import DatasetCreate, DatasetUpdate
from app.schemas.responses import DatasetListResponse, DatasetResponse
from app.utils.logger import logger

router = APIRouter(tags=["dataset"])


@router.get("/dataset", response_model=DatasetListResponse)
def list_dataset(
    query: str = Query("", description="Search by text"),
    intencion: str = Query("", description="Filter by intent name"),
    activo: bool | None = Query(None, description="Filter by active status"),
    conn=Depends(get_db),
):
    items = ctrl.list_dataset(conn, texto_query=query, intencion=intencion, activo=activo)
    return DatasetListResponse(items=[DatasetResponse(**i) for i in items], total=len(items))


@router.post("/dataset", response_model=DatasetResponse, status_code=201)
def create_dataset(req: DatasetCreate, conn=Depends(get_db)):
    item = ctrl.create_dataset(conn, req.texto, req.id_intencion, req.origen)
    logger.info(f"Dataset creado id={item['id']}: {req.texto[:50]}...")
    return DatasetResponse(**item)


@router.put("/dataset/{id}", response_model=DatasetResponse)
def update_dataset(id: int, req: DatasetUpdate, conn=Depends(get_db)):
    item = ctrl.update_dataset(conn, id, req.texto, req.id_intencion)
    if item is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    logger.info(f"Dataset actualizado id={id}")
    return DatasetResponse(**item)


@router.delete("/dataset/{id}")
def delete_dataset(id: int, conn=Depends(get_db)):
    ok = ctrl.delete_dataset(conn, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return {"mensaje": "Dataset desactivado", "id": id}


@router.patch("/dataset/{id}/validar", response_model=DatasetResponse)
def validate_dataset(id: int, conn=Depends(get_db)):
    item = ctrl.validate_dataset(conn, id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    logger.info(f"Dataset validado id={id}")
    return DatasetResponse(**item)

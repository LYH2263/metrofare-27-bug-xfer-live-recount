from fastapi import APIRouter, HTTPException
from app.services.metro_service import MetroService

router = APIRouter(tags=["history"])

@router.get("/history")
def history(limit: int = 50):
    with MetroService() as s:
        return {"items": s.history(limit)}


@router.get("/history/{run_id}")
def history_detail(run_id: int):
    with MetroService() as s:
        row = s.history_item(run_id)
        if row is None:
            raise HTTPException(404, f"记录 {run_id} 不存在")
        return row

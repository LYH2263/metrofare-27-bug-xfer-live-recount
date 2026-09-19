from fastapi import APIRouter

from app.modules.transfer_penalty import router as transfer_penalty
from app.routers import dashboard, edges, fares, history, quote, settings, stations

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, fares, quote, history, settings, transfer_penalty):
    api.include_router(r.router)

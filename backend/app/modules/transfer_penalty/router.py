from fastapi import APIRouter, HTTPException

from app.modules.transfer_penalty.schemas import TransferRuleIn, TransferRuleUpdate
from app.modules.transfer_penalty.service import RuleConflictError, RuleNotFoundError
from app.services.metro_service import MetroService

router = APIRouter(tags=["transfer-rules"])


@router.get("/transfer-rules")
def list_transfer_rules():
    with MetroService() as s:
        return {"items": s.transfer_rules()}


@router.post("/transfer-rules", status_code=201)
def create_transfer_rule(body: TransferRuleIn):
    try:
        with MetroService() as s:
            return s.create_transfer_rule(
                body.from_line, body.to_line, body.surcharge, body.active
            )
    except RuleConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.put("/transfer-rules/{rule_id}")
def update_transfer_rule(rule_id: int, body: TransferRuleUpdate):
    try:
        with MetroService() as s:
            return s.update_transfer_rule(
                rule_id,
                from_line=body.from_line,
                to_line=body.to_line,
                surcharge=body.surcharge,
                active=body.active,
            )
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuleConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/transfer-rules/{rule_id}/deactivate")
def deactivate_transfer_rule(rule_id: int):
    try:
        with MetroService() as s:
            return s.deactivate_transfer_rule(rule_id)
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

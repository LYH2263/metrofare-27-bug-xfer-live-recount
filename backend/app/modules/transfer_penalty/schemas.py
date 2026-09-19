from pydantic import BaseModel


class TransferRuleIn(BaseModel):
    from_line: str
    to_line: str
    surcharge: float
    active: bool = True


class TransferRuleUpdate(BaseModel):
    from_line: str | None = None
    to_line: str | None = None
    surcharge: float | None = None
    active: bool | None = None

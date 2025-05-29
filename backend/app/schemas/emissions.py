from pydantic import BaseModel
from datetime import datetime

class EmissionBase(BaseModel):
    source: str
    value: float
    unit: str

class EmissionCreate(EmissionBase):
    pass

class EmissionRead(EmissionBase):
    id: int
    timestamp: datetime

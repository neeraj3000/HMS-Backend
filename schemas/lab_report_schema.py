from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LabReportBase(BaseModel):
    prescription_id: int
    test_name: str

class LabReportCreate(LabReportBase):
    pass

class LabReportUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None

class LabReportResponse(LabReportBase):
    id: int
    status: str
    result: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class IndentBase(BaseModel):
    file_name: str
    file_url: str
    uploaded_by: str
    status: str
    uploaded_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

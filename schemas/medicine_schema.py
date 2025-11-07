from pydantic import BaseModel
from typing import Optional
from datetime import date

class MedicineBase(BaseModel):
    name: str
    category: Optional[str] = None
    quantity: int
    expiry_date: Optional[date] = None

class MedicineCreate(MedicineBase):
    pass

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    expiry_date: Optional[date] = None

class MedicineResponse(MedicineBase):
    id: int
    class Config:
        from_attributes = True

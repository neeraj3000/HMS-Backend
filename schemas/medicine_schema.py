from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Base Schema
class MedicineBase(BaseModel):
    name: str = Field(..., example="Paracetamol")
    brand: Optional[str] = Field(None, example="Cipla")
    quantity: int = Field(0, example=100)
    cost: Optional[float] = Field(None, example=10.5)
    tax: Optional[float] = Field(None, example=1.8)
    total_cost: Optional[float] = Field(None, example=12.3)
    category: Optional[str] = Field(None, example="Antibiotic")
    expiry_date: Optional[date] = Field(None, example="2025-06-30")


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    quantity: Optional[int] = None
    cost: Optional[float] = None
    tax: Optional[float] = None
    total_cost: Optional[float] = None

    category: Optional[str] = None
    expiry_date: Optional[date] = None


class MedicineResponse(MedicineBase):
    id: int

    class Config:
        from_attributes = True

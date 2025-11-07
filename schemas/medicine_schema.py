from pydantic import BaseModel, Field
from typing import Optional


# Base Schema
class MedicineBase(BaseModel):
    name: str = Field(..., example="Paracetamol")
    brand: Optional[str] = Field(None, example="Cipla")
    quantity: int = Field(0, example=100)
    cost: Optional[float] = Field(None, example=10.5)
    tax: Optional[float] = Field(None, example=1.8)
    total_cost: Optional[float] = Field(None, example=12.3)


# Create Schema
class MedicineCreate(MedicineBase):
    pass


# Update Schema
class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Paracetamol")
    brand: Optional[str] = Field(None, example="Cipla")
    quantity: Optional[int] = Field(None, example=50)
    cost: Optional[float] = Field(None, example=10.5)
    tax: Optional[float] = Field(None, example=1.8)
    total_cost: Optional[float] = Field(None, example=12.3)


# Response Schema
class MedicineResponse(MedicineBase):
    id: int = Field(..., example=1)

    class Config:
        from_attributes = True

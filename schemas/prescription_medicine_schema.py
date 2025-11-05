from pydantic import BaseModel
from typing import Optional

class PrescriptionMedicineBase(BaseModel):
    prescription_id: int
    medicine_id: int
    quantity_prescribed: int

class PrescriptionMedicineCreate(PrescriptionMedicineBase):
    pass

class PrescriptionMedicineUpdate(BaseModel):
    quantity_issued: Optional[int] = None

class PrescriptionMedicineResponse(PrescriptionMedicineBase):
    id: int
    quantity_issued: Optional[int]
    class Config:
        orm_mode = True

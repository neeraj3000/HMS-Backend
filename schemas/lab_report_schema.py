from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from schemas.prescription_schema import PrescriptionResponse
from schemas.student_schema import StudentOut
from schemas.prescription_medicine_schema import PrescriptionMedicineResponse
from schemas.medicine_schema import MedicineResponse


# -------------------- Base Schemas --------------------
class LabReportBase(BaseModel):
    prescription_id: int
    test_name: str


class LabReportCreate(LabReportBase):
    pass


class LabReportUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None
    result_url: Optional[str] = None


class LabReportResponse(LabReportBase):
    id: int
    status: str
    result: Optional[str]
    result_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# -------------------- Nested Response Schemas --------------------
class NestedPrescriptionMedicineResponse(PrescriptionMedicineResponse):
    medicine: MedicineResponse


class NestedPrescriptionResponse(PrescriptionResponse):
    student: StudentOut
    medicines: List[NestedPrescriptionMedicineResponse] = []


class LabReportDetailedResponse(LabReportResponse):
    prescription: NestedPrescriptionResponse

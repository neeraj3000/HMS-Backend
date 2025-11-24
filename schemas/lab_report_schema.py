# schemas/lab_report_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from schemas.student_schema import StudentOut


# ---------------- Base Schemas ----------------
class LabReportBase(BaseModel):
    test_name: str


class LabReportCreate(BaseModel):
    prescription_id: int
    test_name: str


class LabReportUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None
    result_url: Optional[str] = None


# ---------------- Response Schemas ----------------
class LabReportResponse(BaseModel):
    id: int
    prescription_id: Optional[int] = None   # <-- FIXED (previously: int)
    test_name: str
    status: str
    result: Optional[str]
    result_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # additional fields
    patient_type: Optional[str] = None
    visit_type: Optional[str] = None
    other_name: Optional[str] = None

    class Config:
        from_attributes = True


# --------------- Nested Prescription Summary ---------------
class PrescriptionSummary(BaseModel):
    id: int
    nurse_id: Optional[int] = None
    doctor_id: Optional[int] = None
    nurse_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    patient_type: Optional[str] = None
    visit_type: Optional[str] = None
    other_name: Optional[str] = None
    age: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------- Detailed Lab Report ----------------
class LabReportDetailedResponse(LabReportResponse):
    prescription: Optional[PrescriptionSummary] = None
    student: Optional[StudentOut] = None

    class Config:
        from_attributes = True

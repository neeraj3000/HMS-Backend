from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Medicine Entry (for emergency prescriptions)
class MedicineEntry(BaseModel):
    medicine_id: int
    quantity: int


# BASE SCHEMA (common incoming/outgoing fields)
class PrescriptionBase(BaseModel):
    student_id: Optional[int] = None          # null for others
    other_name: Optional[str] = None          # for others

    nurse_id: int

    nurse_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    ai_summary: Optional[str] = None

    nurse_image_url: Optional[str] = None
    doctor_image_url: Optional[str] = None
    audio_url: Optional[str] = None

    weight: Optional[str] = None
    bp: Optional[str] = None
    age: Optional[int] = None
    temperature: Optional[str] = None

    patient_type: Optional[str] = None       # "student" | "others"
    visit_type: Optional[str] = None         # "normal" | "emergency"

    status: Optional[str] = None             # auto-set by backend/doctor


# CREATE SCHEMA
class PrescriptionCreate(PrescriptionBase):
    medicines: Optional[List[MedicineEntry]] = None  # nurse emergency meds
    lab_tests: Optional[List[str]] = None            # nurse emergency labs


# UPDATE SCHEMA (doctor endpoint)
class PrescriptionUpdate(BaseModel):
    doctor_id: Optional[int] = None
    doctor_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    doctor_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    status: Optional[str] = None


# RESPONSE SCHEMA
class PrescriptionResponse(PrescriptionBase):
    id: int
    doctor_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

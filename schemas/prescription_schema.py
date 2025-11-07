from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PrescriptionBase(BaseModel):
    student_id: int
    nurse_id: int
    nurse_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    nurse_image_url: Optional[str] = None
    doctor_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    weight: Optional[str] = None
    bp: Optional[str] = None
    age: Optional[int] = None
    temperature: Optional[str] = None

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionUpdate(BaseModel):
    doctor_id: Optional[int] = None
    nurse_notes: Optional[str] = None
    doctor_notes: Optional[str] = None
    nurse_image_url: Optional[str] = None
    doctor_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    weight: Optional[str] = None
    bp: Optional[str] = None
    age: Optional[int] = None
    temperature: Optional[str] = None
    status: Optional[str] = None

class PrescriptionResponse(PrescriptionBase):
    id: int
    doctor_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

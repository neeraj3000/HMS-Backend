from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

from schemas.prescription_schema import MedicineEntry


class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"
    pharmacist = "pharmacist"
    lab_technician = "lab_technician"
    store_keeper = "store_keeper"
    student = "student"


class UserBase(BaseModel):
    username: str
    email: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    role: Optional[UserRole]


class UserOut(UserBase):
    id: int
    class Config:
        from_attributes = True


class StudentBase(BaseModel):
    id_number: str
    email: str
    name: str
    branch: Optional[str]
    section: Optional[str]


class StudentOut(StudentBase):
    id: int
    class Config:
        from_attributes = True


class MedicineBase(BaseModel):
    name: str
    brand: Optional[str] = None
    quantity: Optional[int] = 0
    cost: Optional[float] = None
    tax: Optional[float] = None
    total_cost: Optional[float] = None


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    quantity: Optional[int] = None
    cost: Optional[float] = None
    tax: Optional[float] = None
    total_cost: Optional[float] = None


class MedicineOut(MedicineBase):
    id: int

    class Config:
        from_attributes = True


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

    patient_type: Optional[str] = None       
    visit_type: Optional[str] = None        

    status: Optional[str] = None             


# CREATE SCHEMA
class PrescriptionCreate(PrescriptionBase):
    medicines: Optional[List[MedicineEntry]] = None  
    lab_tests: Optional[List[str]] = None            


# UPDATE SCHEMA (doctor endpoint)
class PrescriptionUpdate(BaseModel):
    doctor_id: Optional[int] = None
    doctor_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    doctor_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    status: Optional[str] = None


# RESPONSE SCHEMA
class PrescriptionOut(PrescriptionBase):
    id: int
    doctor_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    totalPatientsToday: int
    totalPrescriptions: int
    pendingLabTests: int
    lowStockMedicines: int
    activeUsers: int
    totalStudents: int
    totalStockValue: float


class MedicineAnalytics(BaseModel):
    name: str
    prescriptionCount: int
    stockLevel: int


class AnomalyAlert(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    timestamp: datetime
    details: Optional[str]

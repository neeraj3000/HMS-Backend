from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from enum import Enum


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
        orm_mode = True


class StudentBase(BaseModel):
    id_number: str
    email: str
    name: str
    branch: Optional[str]
    section: Optional[str]


class StudentOut(StudentBase):
    id: int
    class Config:
        orm_mode = True


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
        orm_mode = True


class PrescriptionOut(BaseModel):
    id: int
    student_id: int
    nurse_id: int
    doctor_id: Optional[int]
    nurse_notes: Optional[str]
    doctor_notes: Optional[str]
    nurse_image_url: Optional[str]
    doctor_image_url: Optional[str]
    audio_url: Optional[str]
    weight: Optional[str]
    bp: Optional[str]
    temperature: Optional[str]
    age: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


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

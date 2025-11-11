from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class StaffProfileBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    employeeId: str
    department: Optional[str] = None
    position: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None
    joinDate: Optional[date] = None
    address: Optional[str] = None
    licenseNumber: Optional[str] = None

class StaffProfileCreate(StaffProfileBase):
    user_id: int

class StaffProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    qualification: Optional[str] = None
    experience: Optional[str] = None
    joinDate: Optional[date] = None
    address: Optional[str] = None
    licenseNumber: Optional[str] = None

class StaffProfileResponse(StaffProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

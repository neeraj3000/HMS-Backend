from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"
    pharmacist = "pharmacist"
    lab_technician = "lab_technician"
    store_keeper = "store_keeper"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class GoogleLogin(BaseModel):
    token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    username: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True

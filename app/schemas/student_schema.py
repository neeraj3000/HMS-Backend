from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentBase(BaseModel):
    id_number: str
    email: EmailStr
    name: str
    branch: Optional[str] = None
    section: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    id_number: str
    email: EmailStr
    name: str
    branch: Optional[str] = None
    section: Optional[str] = None
    role: str = "student"
    class Config:
        orm_mode = True

from sqlalchemy import Column, Integer, String, Enum
from database import Base
import enum

class UserRole(enum.Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"
    pharmacist = "pharmacist"
    lab_technician = "lab_technician"
    store_keeper = "store_keeper"
    student = "student"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)

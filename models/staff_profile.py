from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Required fields
    name = Column(String(255), nullable=False)   # take from username
    email = Column(String(255), unique=True, nullable=False)

    # Optional fields
    phone = Column(String(20), nullable=True)
    employeeId = Column("employeeid", String(50), unique=True, nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    qualification = Column(String(255), nullable=True)
    experience = Column(String(50), nullable=True)
    joinDate = Column("joindate", Date, nullable=True)
    address = Column(String(255), nullable=True)
    licenseNumber = Column("licensenumber", String(100), nullable=True)

    user = relationship("User", back_populates="staff_profile")

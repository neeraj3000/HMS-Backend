from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    employeeId = Column("employeeid", String(50), unique=True, nullable=False)  # 👈 FIX
    department = Column(String(100))
    position = Column(String(100))
    qualification = Column(String(255))
    experience = Column(String(50))
    joinDate = Column("joindate", Date)  # 👈 FIX for consistency
    address = Column(String(255))
    licenseNumber = Column("licensenumber", String(100))  # 👈 FIX for consistency

    user = relationship("User", back_populates="staff_profile")

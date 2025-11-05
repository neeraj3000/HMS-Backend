from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)

    # Link to Student table
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    nurse_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Updated field name
    nurse_notes = Column(Text, nullable=True)

    # New optional fields
    doctor_notes = Column(Text, nullable=True)
    nurse_image_url = Column(String(255), nullable=True)
    doctor_image_url = Column(String(255), nullable=True)
    audio_url = Column(String(255), nullable=True)

    # Vitals
    weight = Column(String(20), nullable=True)
    bp = Column(String(20), nullable=True)
    temperature = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)

    status = Column(String(50), default="Initiated by Nurse")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    nurse = relationship("User", foreign_keys=[nurse_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

    # Relationships
    medicines = relationship("PrescriptionMedicine", back_populates="prescription")
    lab_reports = relationship("LabReport", back_populates="prescription")
    student = relationship("Student")

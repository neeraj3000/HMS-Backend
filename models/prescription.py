from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)

    # Student ID is now optional
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)

    # New field for "Others" patients
    other_name = Column(String(255), nullable=True)

    nurse_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    nurse_notes = Column(Text, nullable=True)
    doctor_notes = Column(Text, nullable=True)

    nurse_image_url = Column(String(255), nullable=True)
    doctor_image_url = Column(String(255), nullable=True)
    audio_url = Column(String(255), nullable=True)
    ai_summary = Column(Text, nullable=True)

    # Vitals
    weight = Column(String(20), nullable=True)
    bp = Column(String(20), nullable=True)
    temperature = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)

    patient_type = Column(String(20), nullable=True)   # "student" | "others"
    visit_type = Column(String(20), nullable=True)     # "normal" | "emergency"

    status = Column(String(50), default="Initiated by Nurse")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    nurse = relationship("User", foreign_keys=[nurse_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

    medicines = relationship("PrescriptionMedicine", back_populates="prescription")
    lab_reports = relationship("LabReport", back_populates="prescription")

    student = relationship("Student")

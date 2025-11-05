from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PrescriptionMedicine(Base):
    __tablename__ = "prescription_medicines"

    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity_prescribed = Column(Integer, nullable=False)
    quantity_issued = Column(Integer, nullable=True)  # set when pharmacist issues

    prescription = relationship("Prescription", back_populates="medicines")
    medicine = relationship("Medicine")

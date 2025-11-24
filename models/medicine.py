from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    quantity = Column(Integer, default=0)
    cost = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    category = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True)

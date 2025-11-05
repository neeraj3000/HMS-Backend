from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Indent(Base):
    __tablename__ = "indents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / approved / rejected
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)

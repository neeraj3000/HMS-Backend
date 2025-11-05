from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services import admin_service
from schemas.admin_schemas import (
    DashboardStats,
    UserOut, StudentOut, MedicineOut, PrescriptionOut,
    MedicineAnalytics, AnomalyAlert
)
from typing import List


def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStats:
    return admin_service.get_dashboard_stats(db)

def get_users(db: Session = Depends(get_db)) -> List[UserOut]:
    return admin_service.get_all_users(db)

def create_user(user_data, db: Session = Depends(get_db)) -> UserOut:
    return admin_service.create_user(db, user_data)

def update_user(id: int, user_data, db: Session = Depends(get_db)) -> UserOut:
    user = admin_service.update_user(db, id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def delete_user(id: int, db: Session = Depends(get_db)):
    user = admin_service.delete_user(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Deleted successfully"}

def get_students(db: Session = Depends(get_db)) -> List[StudentOut]:
    return admin_service.get_all_students(db)

def get_student_by_id(id: int, db: Session = Depends(get_db)) -> StudentOut:
    student = admin_service.get_student_by_id(db, id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

def get_prescriptions(db: Session = Depends(get_db)) -> List[PrescriptionOut]:
    return admin_service.get_all_prescriptions(db)

def get_medicines(db: Session = Depends(get_db)) -> List[MedicineOut]:
    return admin_service.get_all_medicines(db)

def create_medicine(data, db: Session = Depends(get_db)) -> MedicineOut:
    return admin_service.create_medicine(db, data)

def update_medicine(id: int, data, db: Session = Depends(get_db)) -> MedicineOut:
    medicine = admin_service.update_medicine(db, id, data)
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine

def delete_medicine(id: int, db: Session = Depends(get_db)):
    medicine = admin_service.delete_medicine(db, id)
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return {"message": "Deleted successfully"}

def get_medicine_analytics(db: Session = Depends(get_db)):
    return admin_service.get_medicine_analytics(db)

def get_anomalies(db: Session = Depends(get_db)):
    return admin_service.get_anomalies(db)

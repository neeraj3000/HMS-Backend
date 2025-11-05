from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from controllers import admin_controller
from schemas.admin_schemas import (
    DashboardStats, UserOut, StudentOut, PrescriptionOut,
    MedicineOut, MedicineAnalytics, AnomalyAlert
)
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard-stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    return admin_controller.get_dashboard_stats(db)

@router.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    return admin_controller.get_users(db)

@router.post("/users", response_model=UserOut)
def create_user(user_data: dict, db: Session = Depends(get_db)):
    return admin_controller.create_user(user_data, db)

@router.put("/users/{id}", response_model=UserOut)
def update_user(id: int, user_data: dict, db: Session = Depends(get_db)):
    return admin_controller.update_user(id, user_data, db)

@router.delete("/users/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    return admin_controller.delete_user(id, db)

@router.get("/students", response_model=List[StudentOut])
def get_students(db: Session = Depends(get_db)):
    return admin_controller.get_students(db)

@router.get("/students/{id}", response_model=StudentOut)
def get_student(id: int, db: Session = Depends(get_db)):
    return admin_controller.get_student_by_id(id, db)

@router.get("/prescriptions", response_model=List[PrescriptionOut])
def get_prescriptions(db: Session = Depends(get_db)):
    return admin_controller.get_prescriptions(db)

@router.get("/medicines", response_model=List[MedicineOut])
def get_medicines(db: Session = Depends(get_db)):
    return admin_controller.get_medicines(db)

@router.post("/medicines", response_model=MedicineOut)
def create_medicine(data: dict, db: Session = Depends(get_db)):
    return admin_controller.create_medicine(data, db)

@router.put("/medicines/{id}", response_model=MedicineOut)
def update_medicine(id: int, data: dict, db: Session = Depends(get_db)):
    return admin_controller.update_medicine(id, data, db)

@router.delete("/medicines/{id}")
def delete_medicine(id: int, db: Session = Depends(get_db)):
    return admin_controller.delete_medicine(id, db)

@router.get("/analytics/medicines", response_model=List[MedicineAnalytics])
def get_medicine_analytics(db: Session = Depends(get_db)):
    return admin_controller.get_medicine_analytics(db)

@router.get("/anomalies", response_model=List[AnomalyAlert])
def get_anomalies(db: Session = Depends(get_db)):
    return admin_controller.get_anomalies(db)

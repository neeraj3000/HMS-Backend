from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.staff_profile import StaffProfile
from models.student import Student
from models.user import User
from models.prescription import Prescription
from models.lab_report import LabReport
from models.prescription_medicine import PrescriptionMedicine
from models.medicine import Medicine
from schemas.admin_schemas import DashboardStats, MedicineAnalytics, AnomalyAlert
from datetime import date, datetime

def get_dashboard_stats(db: Session) -> DashboardStats:
    today = date.today()

    # Total patients visited today (based on prescriptions created today)
    total_patients_today = (
        db.query(func.count(Prescription.id))
        .filter(func.date(Prescription.created_at) == today)
        .scalar()
    )

    # Total prescriptions
    total_prescriptions = db.query(func.count(Prescription.id)).scalar()

    # Pending lab tests (where LabReport.status = "Lab Test Requested")
    pending_lab_tests = (
        db.query(func.count(LabReport.id))
        .filter(LabReport.status == "Lab Test Requested")
        .scalar()
    )

    # Low stock medicines (quantity < 10)
    low_stock_medicines = (
        db.query(func.count(Medicine.id))
        .filter(Medicine.quantity < 10)
        .scalar()
    )

    # Active users (assuming all users are active)
    active_users = db.query(func.count(User.id)).scalar()

    # Total students
    total_students = db.query(func.count(Student.id)).scalar()

    total_stock_value = db.query(
        func.coalesce(func.sum(Medicine.total_cost), 0)
    ).scalar()

    return DashboardStats(
        totalPatientsToday=total_patients_today,
        totalPrescriptions=total_prescriptions,
        pendingLabTests=pending_lab_tests,
        lowStockMedicines=low_stock_medicines,
        activeUsers=active_users,
        totalStudents=total_students,
        totalStockValue=total_stock_value,
    )

# ---------------------- USERS -----------------------
def get_all_users(db: Session):
    return db.query(User).all()

def create_user(db: Session, user_data):
    try:
        # Create User
        user = User(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,  # hash later
            role=user_data.role
        )
        db.add(user)
        db.flush()  # ensures user.id is available

        # Create StaffProfile with ONLY USER DATA
        profile = StaffProfile(
            user_id=user.id,
            name=user_data.username,
            email=user_data.email,
            phone=None,
            employeeId=None,
            department=None,
            position=None,
            qualification=None,
            experience=None,
            joinDate=None,
            address=None,
            licenseNumber=None
        )

        db.add(profile)

        # Commit both
        db.commit()
        db.refresh(user)

        return user

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

def update_user(db: Session, user_id: int, user_data):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for key, value in user_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user

# ---------------------- STUDENTS -----------------------
def get_all_students(db: Session):
    return db.query(Student).all()

def get_student_by_id(db: Session, id: int):
    return db.query(Student).filter(Student.id == id).first()

# ---------------------- PRESCRIPTIONS -----------------------
def get_all_prescriptions(db: Session):
    return db.query(Prescription).all()

# ---------------------- MEDICINES -----------------------
def get_all_medicines(db: Session):
    return db.query(Medicine).all()

def create_medicine(db: Session, medicine_data):
    medicine = Medicine(**medicine_data)
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine

def update_medicine(db: Session, id: int, data):
    medicine = db.query(Medicine).filter(Medicine.id == id).first()
    if not medicine:
        return None
    for key, value in data.items():
        setattr(medicine, key, value)
    db.commit()
    db.refresh(medicine)
    return medicine

def delete_medicine(db: Session, id: int):
    medicine = db.query(Medicine).filter(Medicine.id == id).first()
    if medicine:
        db.delete(medicine)
        db.commit()
    return medicine

# ---------------------- ANALYTICS -----------------------
def get_medicine_analytics(db: Session):
    """
    Returns analytics for each medicine:
    - name
    - number of prescriptions that included it
    - current stock level
    """

    results = (
        db.query(
            Medicine.name.label("name"),
            func.count(PrescriptionMedicine.id).label("prescriptionCount"),
            Medicine.quantity.label("stockLevel")
        )
        .outerjoin(PrescriptionMedicine, Medicine.id == PrescriptionMedicine.medicine_id)
        .group_by(Medicine.id)
        .all()
    )

    analytics = [
        {
            "name": r.name,
            "prescriptionCount": r.prescriptionCount,
            "stockLevel": r.stockLevel,
        }
        for r in results
    ]

    return analytics

# ---------------------- ANOMALIES -----------------------
def get_anomalies(db: Session):
    return [
        AnomalyAlert(
            id="1",
            type="StockMismatch",
            severity="medium",
            message="Mismatch between recorded and actual stock.",
            timestamp=datetime.now(),
            details="Medicine X count mismatch",
        )
    ]

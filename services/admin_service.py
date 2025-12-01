import json
import os
from fastapi import HTTPException
import requests
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
from dotenv import load_dotenv
load_dotenv()

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

    total_stock_value = (
        db.query(func.sum(Medicine.quantity * func.coalesce(Medicine.cost, 0)))
        .scalar()
        or 0
    )

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
AI_URL = os.getenv("AI_URL", "https://api.openai.com/v1/chat/completions")
AI_KEY = os.getenv("AI_KEY")


def call_ai(prompt: str):
    """
    Handles AI call (OpenAI / custom model / LM Studio / FastAPI LLM server).
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_KEY}"
    }

    body = {
        "model": "gpt-4o-mini",     # Change as needed
        "messages": [
            {"role": "system", "content": "You are an anomaly detection engine."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
    }

    response = requests.post(AI_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def get_anomalies(db: Session):
    """
    Collect all hospital data & send to AI model for anomaly detection.
    """

    # ---- 1. Collect medicines ----
    medicines = db.query(Medicine).all()
    medicines_data = [
        {
            "id": m.id,
            "name": m.name,
            "brand": m.brand,
            "category": m.category,
            "expiry_date": m.expiry_date.isoformat() if m.expiry_date else None,
            "quantity": m.quantity,
            "cost": m.cost,
            "tax": m.tax,
            "total_cost": m.total_cost,
        }
        for m in medicines
    ]

    # ---- 2. Collect prescriptions ----
    prescriptions = db.query(Prescription).all()
    prescriptions_data = [
        {
            "id": p.id,
            "student_id": p.student_id,
            "other_name": p.other_name,
            "patient_type": p.patient_type,
            "visit_type": p.visit_type,
            "status": p.status,
            "age": p.age,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in prescriptions
    ]

    # ---- 3. Collect medicine usage ----
    prescribed_data = db.query(PrescriptionMedicine).all()
    prescribed_usage = [
        {
            "prescription_id": pm.prescription_id,
            "medicine_id": pm.medicine_id,
            "quantity_prescribed": pm.quantity_prescribed,
            "quantity_issued": pm.quantity_issued,
        }
        for pm in prescribed_data
    ]

    # ---- 4. Collect lab reports ----
    lab_reports = db.query(LabReport).all()
    lab_reports_data = [
        {
            "id": lr.id,
            "prescription_id": lr.prescription_id,
            "test_name": lr.test_name,
            "status": lr.status,
            "result_uploaded": bool(lr.result or lr.result_url),
        }
        for lr in lab_reports
    ]

    # ---- 5. Collect students ----
    students = db.query(Student).all()
    students_data = [
        {
            "id": s.id,
            "id_number": s.id_number,
            "name": s.name,
            "branch": s.branch,
            "section": s.section,
            "email": s.email,
        }
        for s in students
    ]

    # ---- 6. Construct dataset ----
    full_dataset = {
        "timestamp": datetime.now().isoformat(),
        "medicines": medicines_data,
        "prescriptions": prescriptions_data,
        "medicine_usage": prescribed_usage,
        "lab_reports": lab_reports_data,
        "students": students_data,
    }

    # Convert to text for AI
    dataset_json = json.dumps(full_dataset, indent=2)

    # ---- 7. Send prompt to AI ----
    prompt = f"""
        You are an expert AI anomaly detection engine for a Hospital Management System.

        Analyze the following dataset and identify ALL types of anomalies:

        Dataset:
        {dataset_json}

        Find anomalies in:

        1. **Medicine Inventory**
        - Negative stock
        - Expired medicines
        - Quantity issued > stock
        - Inconsistent total_cost
        - Missing categories
        - Expiry date too near
        - Medicine prescribed but not in stock

        2. **Prescriptions**
        - Prescription with no medicines issued
        - Missing vital fields
        - Invalid patient type
        - Duplicate prescriptions
        - Wrong status flows

        3. **Medicine Usage**
        - quantity_issued > quantity_prescribed
        - Missing prescription reference

        4. **Lab Reports**
        - Completed without result uploaded
        - Pending for too long
        - Lab report without prescription

        5. **Students**
        - Duplicate ID numbers
        - Missing fields

        Return output in JSON EXACTLY like this:
        {{
        "anomalies": [
            {{
            "type": "StockMismatch",
            "severity": "high",
            "message": "",
            "details": ""
            }}
        ]
        }}
    """

    result = call_ai(prompt)

    return {
        "success": True,
        "generated_at": datetime.now(),
        "anomalies": json.loads(result)
    }

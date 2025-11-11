from sqlalchemy.orm import Session
from models.prescription import Prescription
from models.lab_report import LabReport
from sqlalchemy import func
from datetime import datetime, timedelta, date

def get_hospital_stats(db: Session):
    today = date.today()

    # Total patients visited today (based on prescriptions created today)
    total_patients_today = (
        db.query(func.count(Prescription.id))
        .filter(func.date(Prescription.created_at) == today)
        .scalar()
    )
    total_prescriptions = db.query(Prescription).count()
    pending_prescriptions = db.query(Prescription).filter(Prescription.status == "Initiated by Nurse").count()
    # completed_prescriptions = db.query(Prescription).filter(Prescription.status == "completed").count()
    lab_reports_pending = db.query(LabReport).filter(LabReport.status == "Lab Test Requested").count()

    return {
        "totalPatientsToday": total_patients_today,
        "totalPrescriptions": total_prescriptions,
        "pendingPrescriptions": pending_prescriptions,
        "pendingLabTests": lab_reports_pending
    }


def get_lab_tech_stats(db: Session):
    today = date.today()
    now = datetime.utcnow()

    # Calculate 24-hour cutoff
    cutoff_time = now - timedelta(hours=24)

    # Pending tests (status = "Lab Test Requested")
    pending_tests = db.query(LabReport).filter(
        LabReport.status == "Lab Test Requested"
    ).count()

    # Completed today (created today and status = "Lab Test Completed")
    completed_today = db.query(LabReport).filter(
        LabReport.status == "Lab Test Completed",
        LabReport.updated_at >= datetime.combine(today, datetime.min.time())
    ).count()

    # Total tests
    total_tests = db.query(LabReport).count()

    # Urgent tests (older than 24 hours and still pending)
    urgent_tests = db.query(LabReport).filter(
        LabReport.status == "Lab Test Requested",
        LabReport.created_at <= cutoff_time
    ).count()

    return {
        "pendingTests": pending_tests,
        "completedToday": completed_today,
        "totalTests": total_tests,
        "urgentTests": urgent_tests
    }

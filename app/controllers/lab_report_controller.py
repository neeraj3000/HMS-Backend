from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from models.prescription import Prescription
from models.lab_report import LabReport
from schemas.lab_report_schema import LabReportCreate, LabReportUpdate

from sqlalchemy.orm import Session, joinedload

def get_lab_reports(db: Session, skip: int = 0, limit: int = 100):
    """
    Fetch all lab reports along with their related prescription and student details.
    """
    return (
        db.query(LabReport)
        .options(
            joinedload(LabReport.prescription)  # load Prescription
            .joinedload(Prescription.student)   # load related Student
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_lab_report(db: Session, report_id: int):
    """
    Fetch a single lab report by ID along with its related prescription and student details.
    """
    return (
        db.query(LabReport)
        .options(
            joinedload(LabReport.prescription)
            .joinedload(Prescription.student)
            .joinedload(Prescription.medicines)
            .joinedload(Prescription.lab_reports)
        )
        .filter(LabReport.id == report_id)
        .first()
    )

def create_lab_report(db: Session, lab_report: LabReportCreate):
    db_lab_report = LabReport(**lab_report.dict())
    db.add(db_lab_report)
    db.commit()
    db.refresh(db_lab_report)
    return db_lab_report

def update_lab_report(db: Session, report_id: int, lab_report: LabReportUpdate):
    """
    Update a lab report and automatically update the corresponding prescription status
    based on medicines and lab report conditions.
    """
    db_report = get_lab_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Lab report not found")

    # --- Update lab report fields ---
    for field, value in lab_report.dict(exclude_unset=True).items():
        setattr(db_report, field, value)
    db.commit()
    db.refresh(db_report)

    # --- Update corresponding prescription status ---
    pres = db_report.prescription
    if pres:
        has_lab_result = any(lr.result for lr in pres.lab_reports)
        has_lab_requested = any(not lr.result for lr in pres.lab_reports)
        has_meds_prescribed = len(pres.medicines) > 0
        has_meds_issued = any(
            getattr(med, "quantity_issued", None)
            for med in pres.medicines
        )

        # Determine prescription status
        if has_meds_issued and has_lab_result:
            pres.status = "Medication issued and Lab Test Completed"
        elif has_meds_issued and has_lab_requested:
            pres.status = "Medication issued and Lab Test Requested"
        elif has_meds_prescribed and not has_meds_issued and has_lab_requested:
            pres.status = "Medication Prescribed and Lab Test Requested"
        elif has_lab_result:
            pres.status = "Lab Test Completed"
        elif has_lab_requested:
            pres.status = "Lab Test Requested"
        elif has_meds_issued:
            pres.status = "Medication Issued by Pharmacist"
        elif has_meds_prescribed:
            pres.status = "Medication Prescribed by Doctor"
        else:
            pres.status = "Initiated by Nurse"

        db.commit()
        db.refresh(pres)

    return db_report

def delete_lab_report(db: Session, report_id: int):
    db_report = get_lab_report(db, report_id)
    if not db_report:
        return None
    db.delete(db_report)
    db.commit()
    return db_report

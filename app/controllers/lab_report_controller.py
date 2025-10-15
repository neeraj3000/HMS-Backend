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
    db_report = get_lab_report(db, report_id)
    if not db_report:
        return None
    for field, value in lab_report.dict(exclude_unset=True).items():
        setattr(db_report, field, value)
    db.commit()
    db.refresh(db_report)
    return db_report

def delete_lab_report(db: Session, report_id: int):
    db_report = get_lab_report(db, report_id)
    if not db_report:
        return None
    db.delete(db_report)
    db.commit()
    return db_report

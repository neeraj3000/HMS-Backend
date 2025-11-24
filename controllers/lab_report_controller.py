# controllers/lab_report_controller.py
from io import BytesIO
import requests
import mimetypes
from urllib.parse import urlparse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, and_, cast, String, case, desc
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO

from models.prescription import Prescription
from models.lab_report import LabReport
from models.prescription_medicine import PrescriptionMedicine
from models.student import Student
from schemas.lab_report_schema import LabReportCreate, LabReportUpdate
from utils.pdf_utils import create_cover_pdf, merge_pdfs, embed_image_into_pdf

from fastapi import HTTPException


def get_lab_reports(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch paginated lab reports with related prescription and student.
    Filters: search (student name / student id / test name / other_name), status, date.
    Orders: 'Lab Test Requested' first, then newest first by created_at.
    """

    if page < 1:
        page = 1
    skip = (page - 1) * limit

    # Use selectinload for efficient eager loading
    query = (
        db.query(LabReport)
        .options(
            selectinload(LabReport.prescription).selectinload(Prescription.student)
        )
        .outerjoin(LabReport.prescription)   # outerjoin to allow prescription/student to be null-safe
        .outerjoin(Prescription.student)     # outerjoin student, because prescription may be for "others"
    )

    filters = []

    # --- Search filter ---
    if search and search.strip():
        s = search.strip()
        search_term = f"%{s}%"
        # include student.name, student.id_number, test_name, prescription.other_name
        filters.append(
            or_(
                Student.name.ilike(search_term),
                Student.id_number.ilike(search_term),
                LabReport.test_name.ilike(search_term),
                Prescription.other_name.ilike(search_term),
                cast(LabReport.id, String).ilike(search_term),
            )
        )

    # --- Status filter ---
    if status and status.lower() != "all":
        filters.append(LabReport.status.ilike(f"%{status}%"))

    # --- Date filter ---
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            filters.append(
                and_(
                    LabReport.created_at >= datetime.combine(date_obj, datetime.min.time()),
                    LabReport.created_at < datetime.combine(date_obj, datetime.max.time()),
                )
            )
        except ValueError:
            pass  # ignore invalid date

    if filters:
        query = query.filter(and_(*filters))

    # --- PRIORITY SORT: "Lab Test Requested" first, then newest ---
    priority_order = case(
        (LabReport.status == "Lab Test Requested", 1),
        else_=2
    ).label("priority")

    query = query.order_by(priority_order, desc(LabReport.created_at))

    # --- Pagination ---
    total = query.count()
    reports = query.offset(skip).limit(limit).all()
    has_more = (page * limit) < total

    # --- Serialization ---
    data = []
    for r in reports:
        pres = r.prescription
        student = pres.student if pres else None

        data.append({
            "id": r.id,
            "test_name": r.test_name,
            "status": r.status,
            "result": r.result,
            "created_at": r.created_at,
            "updated_at": r.updated_at,

            # prescription minimal info
            "prescription": {
                "id": pres.id if pres else None,
                "nurse_id": pres.nurse_id if pres else None,
                "doctor_id": pres.doctor_id if pres else None,
                "nurse_notes": pres.nurse_notes if pres else None,
                "doctor_notes": pres.doctor_notes if pres else None,
                "patient_type": pres.patient_type if pres else None,
                "visit_type": pres.visit_type if pres else None,
                "other_name": pres.other_name if pres else None,
                "created_at": pres.created_at if pres else None,
            } if pres else None,

            # student (nullable) — if student is null, front-end will use prescription.other_name
            "student": {
                "id": student.id if student else None,
                "id_number": student.id_number if student else None,
                "name": student.name if student else None,
                "branch": student.branch if student else None,
                "section": student.section if student else None,
                "email": student.email if student else None
            } if student else None,

            # Top-level convenience fields for front-end
            "patient_type": pres.patient_type if pres else None,
            "visit_type": pres.visit_type if pres else None,
            "other_name": pres.other_name if pres else None,
        })

    return {
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
        "has_more": has_more
    }


def get_lab_report(db: Session, report_id: int):
    """
    Fetch a single lab report by ID along with its related prescription, student, and
    prescription.medicines if required (NOT included here per user choice).
    """
    r = (
        db.query(LabReport)
        .options(
            selectinload(LabReport.prescription)
            .selectinload(Prescription.student),
            selectinload(LabReport.prescription)
            .selectinload(Prescription.lab_reports)
        )
        .filter(LabReport.id == report_id)
        .first()
    )

    if not r:
        return None

    pres = r.prescription
    student = pres.student if pres else None

    # Build a serializable dict (this will match LabReportDetailedResponse schema below)
    result = {
        "id": r.id,
        "test_name": r.test_name,
        "status": r.status,
        "result": r.result,
        "result_url": r.result_url,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
        "prescription": {
            "id": pres.id if pres else None,
            "nurse_id": pres.nurse_id if pres else None,
            "doctor_id": pres.doctor_id if pres else None,
            "nurse_notes": pres.nurse_notes if pres else None,
            "doctor_notes": pres.doctor_notes if pres else None,
            "patient_type": pres.patient_type if pres else None,
            "visit_type": pres.visit_type if pres else None,
            "other_name": pres.other_name if pres else None,
            "age": pres.age if pres else None,
            "created_at": pres.created_at if pres else None,
        } if pres else None,
        "student": {
            "id": student.id if student else None,
            "id_number": student.id_number if student else None,
            "name": student.name if student else None,
            "branch": student.branch if student else None,
            "section": student.section if student else None,
            "email": student.email if student else None
        } if student else None,
    }

    return result


def update_lab_report(db: Session, report_id: int, lab_report: LabReportUpdate):
    """
    Update a lab report and auto-update the corresponding prescription status.
    Returns the updated lab report dict (serialized).
    """
    # Load the DB object (as in original implementation)
    db_report = db.query(LabReport).filter(LabReport.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Lab report not found")

    # Update fields dynamically
    for field, value in lab_report.dict(exclude_unset=True).items():
        setattr(db_report, field, value)
    db.commit()
    db.refresh(db_report)

    # Update corresponding prescription status (existing logic)
    pres = db_report.prescription
    if pres:
        has_lab_result = any(lr.result for lr in pres.lab_reports)
        has_lab_requested = any(not lr.result for lr in pres.lab_reports)
        has_meds_prescribed = len(pres.medicines) > 0
        has_meds_issued = any(
            getattr(med, "quantity_issued", None)
            for med in pres.medicines
        )

        # Determine prescription status (use your exact naming; adjust casing if needed)
        if has_meds_issued and has_lab_result:
            pres.status = "Medication Issued and Lab Test Completed"
        elif has_meds_issued and has_lab_requested:
            pres.status = "Medication Issued and Lab Test Requested"
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

    # Return serialized updated lab report
    return get_lab_report(db, report_id)


def delete_lab_report(db: Session, report_id: int):
    db_report = db.query(LabReport).filter(LabReport.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Lab report not found")

    db.delete(db_report)
    db.commit()
    return {"ok": True}


def generate_lab_report_pdf(db: Session, lab_report) -> (BytesIO, str): # type: ignore
    # ... keep your existing implementation here (no changes)
    cover_buf = create_cover_pdf(lab_report)
    result_url = getattr(lab_report, "result_url", None)
    if not result_url:
        filename = f"LabReport_{lab_report.id}.pdf"
        return cover_buf, filename
    try:
        resp = requests.get(result_url, stream=True, timeout=15)
        resp.raise_for_status()
    except Exception:
        return cover_buf, f"LabReport_{lab_report.id}.pdf"
    content_type = resp.headers.get("Content-Type")
    if not content_type:
        ext = urlparse(result_url).path.split('.')[-1]
        content_type = mimetypes.guess_type(f"file.{ext}")[0] or ""
    if "pdf" in (content_type or "").lower():
        remote_pdf_bytes = BytesIO(resp.content)
        merged = merge_pdfs([cover_buf, remote_pdf_bytes])
        return merged, f"LabReport_{lab_report.id}.pdf"
    if (content_type or "").startswith("image/"):
        image_bytes = BytesIO(resp.content)
        combined = embed_image_into_pdf(cover_buf, image_bytes)
        return combined, f"LabReport_{lab_report.id}.pdf"
    return cover_buf, f"LabReport_{lab_report.id}.pdf"

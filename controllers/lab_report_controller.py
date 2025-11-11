import datetime
from io import BytesIO
import requests
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import mimetypes
from fastapi import HTTPException
from typing import Optional, Dict, Any
from sqlalchemy import or_, and_, cast, String
from sqlalchemy.orm import Session, joinedload, selectinload
from models.prescription import Prescription
from models.lab_report import LabReport
from models.prescription_medicine import PrescriptionMedicine
from models.student import Student
from schemas.lab_report_schema import LabReportCreate, LabReportUpdate
from utils.pdf_utils import create_cover_pdf, merge_pdfs, embed_image_into_pdf


from sqlalchemy import case, desc, or_, and_, func
from typing import Optional, Dict, Any
from datetime import datetime

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
    Filters: search (student name / student id / test name), status, date.
    Orders: 'Lab Test Requested' first, then newest first by created_at.
    """
    if page < 1:
        page = 1
    skip = (page - 1) * limit

    query = (
        db.query(LabReport)
        .options(
            selectinload(LabReport.prescription).selectinload(Prescription.student)
        )
        .join(LabReport.prescription)
        .join(Prescription.student)
    )

    filters = []

    # --- Search filter ---
    if search and search.strip():
        s = search.strip()
        search_term = f"%{s}%"
        student_name_cond = Student.name.ilike(search_term)
        student_idnum_cond = Student.id_number.ilike(search_term)
        test_name_cond = LabReport.test_name.ilike(search_term)
        filters.append(or_(student_name_cond, student_idnum_cond, test_name_cond))

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
            "prescription": {
                "id": pres.id,
                "student_id": pres.student_id,
                "nurse_id": pres.nurse_id,
                "doctor_id": pres.doctor_id,
                "nurse_notes": pres.nurse_notes,
                "doctor_notes": pres.doctor_notes,
                "created_at": pres.created_at,
            } if pres else None,
            "student": {
                "id": student.id if student else None,
                "id_number": student.id_number if student else None,
                "name": student.name if student else None,
                "branch": student.branch if student else None,
                "section": student.section if student else None,
                "email": student.email if student else None
            } if student else None
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
    Fetch a single lab report by ID along with its related prescription, student, and medicine details.
    """
    return (
        db.query(LabReport)
        .options(
            selectinload(LabReport.prescription)
            .selectinload(Prescription.student),
            selectinload(LabReport.prescription)
            .selectinload(Prescription.medicines)
            .selectinload(PrescriptionMedicine.medicine),
            selectinload(LabReport.prescription)
            .selectinload(Prescription.lab_reports)
        )
        .filter(LabReport.id == report_id)
        .first()
    )


def create_lab_report(db: Session, lab_report: LabReportCreate):
    """
    Create a new lab report entry.
    """
    db_lab_report = LabReport(**lab_report.dict())
    db.add(db_lab_report)
    db.commit()
    db.refresh(db_lab_report)
    return db_lab_report


def update_lab_report(db: Session, report_id: int, lab_report: LabReportUpdate):
    """
    Update a lab report and auto-update the corresponding prescription status.
    """
    db_report = get_lab_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Lab report not found")

    # Update fields dynamically
    for field, value in lab_report.dict(exclude_unset=True).items():
        setattr(db_report, field, value)
    db.commit()
    db.refresh(db_report)

    # Update corresponding prescription status
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
    """
    Delete a lab report by ID.
    """
    db_report = get_lab_report(db, report_id)
    if not db_report:
        raise HTTPException(status_code=404, detail="Lab report not found")

    db.delete(db_report)
    db.commit()
    return db_report

def generate_lab_report_pdf(db: Session, lab_report) -> (BytesIO, str): # type: ignore
    """
    Generates a PDF containing:
    - A cover page with report details and a clickable hyperlink to result_url (if present).
    - If result_url points to a PDF: merge that PDF pages after cover.
    - If result_url is an image: embed image pages after cover.
    - Otherwise: only cover with hyperlink.
    Returns (BytesIO_of_result_pdf, filename).
    """
    cover_buf = create_cover_pdf(lab_report)  # BytesIO of the cover page

    result_url = getattr(lab_report, "result_url", None)
    if not result_url:
        # No uploaded file - return cover only
        filename = f"LabReport_{lab_report.id}.pdf"
        return cover_buf, filename

    # Try to fetch the remote file
    try:
        resp = requests.get(result_url, stream=True, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        # Could not fetch file; return cover only (cover already contains hyperlink)
        return cover_buf, f"LabReport_{lab_report.id}.pdf"

    # Determine content-type (prefer header, fallback to extension)
    content_type = resp.headers.get("Content-Type")
    if not content_type:
        # Try to guess from url extension
        ext = urlparse(result_url).path.split('.')[-1]
        content_type = mimetypes.guess_type(f"file.{ext}")[0] or ""

    # If PDF: merge
    if "pdf" in (content_type or "").lower():
        remote_pdf_bytes = BytesIO(resp.content)
        merged = merge_pdfs([cover_buf, remote_pdf_bytes])
        return merged, f"LabReport_{lab_report.id}.pdf"

    # If image: embed image into new pages after cover
    if (content_type or "").startswith("image/"):
        image_bytes = BytesIO(resp.content)
        combined = embed_image_into_pdf(cover_buf, image_bytes)
        return combined, f"LabReport_{lab_report.id}.pdf"

    # Fallback: unknown type — return cover only (which already has hyperlink)
    return cover_buf, f"LabReport_{lab_report.id}.pdf"

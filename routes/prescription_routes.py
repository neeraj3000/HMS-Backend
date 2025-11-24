from io import BytesIO
import cloudinary
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.prescription import Prescription
from controllers import prescription_controller as ctrl
from schemas.prescription_schema import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionResponse,
)
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


# ================================================================
# GET PENDING PRESCRIPTIONS
# ================================================================
@router.get("/pending")
def get_pending_prescriptions(db: Session = Depends(get_db)):
    return ctrl.get_pending_prescriptions(db)


# ================================================================
# GENERAL LIST WITH SEARCH, FILTERS, PAGINATION
# ================================================================
@router.get("/")
def read_prescriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    search: str = Query(None),
    status: str = Query(None),
    date: str = Query(None),
    db: Session = Depends(get_db),
):
    return ctrl.get_prescriptions(db, page, limit, search, status, date)

@router.get("/prescribed-queue")
def prescribed_queue(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    date: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Pharmacist Queue:
    Returns prescriptions ready for medicine issuance:
      - Medication Prescribed by Doctor
      - Medication Prescribed and Lab Test Requested
      - Medication Prescribed by Nurse (Emergency)
    """
    return ctrl.get_prescribed_queue(
        db=db,
        page=page,
        limit=limit,
        search=search,
        date=date,
        status=status,
    )

# ================================================================
# GET BY ID
# ================================================================
@router.get("/{prescription_id}")
def read_prescription(prescription_id: int, db: Session = Depends(get_db)):
    return ctrl.get_prescription(db, prescription_id)


# ================================================================
# GET PRESCRIPTIONS OF A STUDENT
# ================================================================
@router.get("/student/{student_id}")
def get_prescriptions_by_student(
    student_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    search: str = "",
    status: str = "all",
    date: str = None,
    db: Session = Depends(get_db),
):
    return ctrl.get_prescriptions_by_studentid(
        db=db,
        student_id=student_id,
        page=page,
        limit=limit,
        search=search,
        status=status,
        date=date
    )


# ================================================================
# CREATE PRESCRIPTION
# ================================================================
@router.post("/", response_model=PrescriptionResponse)
def create_prescription_route(
    prescription: PrescriptionCreate,
    db: Session = Depends(get_db),
):
    return ctrl.create_prescription(db, prescription)


# ================================================================
# UPDATE WITH AUDIO
# ================================================================
@router.put("/{prescription_id}/update-with-audio")
async def update_prescription_with_audio(
    prescription_id: int,
    doctor_id: int = Form(...),
    doctor_notes: str = Form(...),
    ai_summary: str = Form(None),
    status: str = Form(...),
    doctor_image_url: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    prescription, error = ctrl.update_prescription_with_audio(
        db=db,
        prescription_id=prescription_id,
        doctor_id=doctor_id,
        doctor_notes=doctor_notes,
        ai_summary=ai_summary,
        status=status,
        doctor_image_url=doctor_image_url,
        file=file,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return {
        "success": True,
        "message": "Prescription updated successfully",
        "audio_url": prescription.audio_url,
    }


# ================================================================
# UPDATE PRESCRIPTION
# ================================================================
@router.put("/{prescription_id}")
def update_prescription(
    prescription_id: int,
    prescription: PrescriptionUpdate,
    db: Session = Depends(get_db),
):
    updated = ctrl.update_prescription(db, prescription_id, prescription)
    if not updated:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return updated


# ================================================================
# DELETE PRESCRIPTION
# ================================================================
@router.delete("/{prescription_id}")
def delete_prescription(prescription_id: int, db: Session = Depends(get_db)):
    deleted = ctrl.delete_prescription(db, prescription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return {"ok": True}


# ================================================================
# SIMPLE PAGINATED LIST (ADMIN)
# ================================================================
@router.get("/list", response_model=dict)
def list_prescriptions_endpoint(
    page: int = 1,
    limit: int = 10,
    sortBy: str = "date",
    status: str = "all",
    db: Session = Depends(get_db),
):
    data, total = ctrl.list_prescriptions(db, page, limit, sortBy, status)
    return {"data": data, "total": total}


# ================================================================
# DOWNLOAD PRESCRIPTION PDF
# ================================================================
@router.get("/{prescription_id}/download")
def download_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
):
    pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()

    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setTitle(f"Prescription_{prescription_id}")

    # ============================================================
    # BUILD PDF (NOW SUPPORTS OTHER PATIENTS)
    # ============================================================

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 820, "Medicare Hospital – Prescription")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 790, f"Prescription ID: {pres.id}")

    if pres.student_id:
        pdf.drawString(50, 770, f"Patient Type: Student")
        pdf.drawString(50, 750, f"Student ID: {pres.student_id}")
    else:
        pdf.drawString(50, 770, f"Patient Type: Others")
        pdf.drawString(50, 750, f"Patient Name: {pres.other_name or 'N/A'}")

    pdf.drawString(50, 730, f"Nurse ID: {pres.nurse_id}")
    pdf.drawString(50, 710, f"Doctor ID: {pres.doctor_id or 'Not Assigned'}")

    pdf.drawString(50, 690, f"Age: {pres.age or 'N/A'}")
    pdf.drawString(50, 670, f"Temperature: {pres.temperature or 'N/A'}")
    pdf.drawString(50, 650, f"BP: {pres.bp or 'N/A'}")
    pdf.drawString(50, 630, f"Weight: {pres.weight or 'N/A'}")

    pdf.drawString(50, 610, f"Status: {pres.status}")

    pdf.drawString(50, 580, "Nurse Notes:")
    pdf.drawString(50, 560, pres.nurse_notes or "N/A")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=prescription_{prescription_id}.pdf"
        },
    )
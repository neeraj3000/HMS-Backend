from io import BytesIO
from os import stat
import os
from reportlab.pdfgen import canvas
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from models.prescription import Prescription
from database import get_db
from controllers import prescription_controller as ctrl
from schemas.prescription_schema import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

# Pending first (specific path)
@router.get("/pending")
def get_pending_prescriptions(db: Session = Depends(get_db)):
    """
    Returns all prescriptions with status 'Initiated by Nurse'
    (used by doctor dashboard patient queue)
    """
    prescriptions = ctrl.get_pending_prescriptions(db)
    return prescriptions

# General list
@router.get("/")
def read_prescriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    search: str = Query(None),
    status: str = Query(None),
    date: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get prescriptions with infinite scrolling + filtering.
    """
    return ctrl.get_prescriptions(db, page, limit, search, status, date)

# Get by ID (below pending)
@router.get("/{prescription_id}")
def read_prescription(prescription_id: int, db: Session = Depends(get_db)):
    pres = ctrl.get_prescription(db, prescription_id)
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return pres

@router.get("/student/{student_id}")
def get_pescriptions_by_id(student_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pres = ctrl.get_prescriptions_by_studentid(db, student_id, skip, limit)
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return pres

@router.post("/")
def create_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):
    return ctrl.create_prescription(db, prescription)

@router.put("/{prescription_id}/update-with-audio")
async def update_prescription_with_audio(
    prescription_id: int,
    doctor_id: int = Form(...),
    doctor_notes: str = Form(...),
    ai_summary: str = Form(None),
    status: str = Form(...),
    doctor_image_url: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Unified endpoint:
    - Handles prescription update + optional audio upload
    - Stores Cloudinary audio URL in DB
    """
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

@router.put("/{prescription_id}")
def update_prescription(prescription_id: int, prescription: PrescriptionUpdate, db: Session = Depends(get_db)):
    pres = ctrl.update_prescription(db, prescription_id, prescription)
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return pres

@router.delete("/{prescription_id}")
def delete_prescription(prescription_id: int, db: Session = Depends(get_db)):
    pres = ctrl.delete_prescription(db, prescription_id)
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return {"ok": True}

# (Optional) your paginated list can stay below or merge with above
@router.get("/list", response_model=dict)
def list_prescriptions_endpoint(
    page: int = 1,
    limit: int = 10,
    sortBy: str = "date",
    status: str = "all",
    db: Session = Depends(get_db),
):
    prescriptions, total = ctrl.list_prescriptions(db, page, limit, sortBy, status)
    return {"data": prescriptions, "total": total}

@router.get("/{prescription_id}/download")
def download_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
):
    # Fetch prescription
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=stat.HTTP_404_NOT_FOUND, detail="Prescription not found")

    # Generate PDF dynamically
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setTitle(f"Prescription_{prescription_id}")

    # Add prescription details
    pdf.drawString(50, 820, f"Prescription ID: {prescription.id}")
    pdf.drawString(50, 800, f"Student ID: {prescription.student_id}")
    pdf.drawString(50, 780, f"Nurse ID: {prescription.nurse_id}")
    pdf.drawString(50, 760, f"Doctor ID: {prescription.doctor_id}")
    pdf.drawString(50, 740, f"Nurse Notes: {prescription.nurse_notes or 'N/A'}")
    pdf.drawString(50, 720, f"Doctor Notes: {prescription.doctor_notes or 'N/A'}")
    pdf.drawString(50, 700, f"Weight: {prescription.weight or 'N/A'}")
    pdf.drawString(50, 680, f"BP: {prescription.bp or 'N/A'}")
    pdf.drawString(50, 660, f"Temperature: {prescription.temperature or 'N/A'}")
    pdf.drawString(50, 640, f"Status: {prescription.status}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    # Return as file download
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=prescription_{prescription_id}.pdf"}
    )